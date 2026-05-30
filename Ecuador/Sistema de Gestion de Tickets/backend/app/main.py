


import os
import re
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlparse, urlunparse
from uuid import uuid4

import httpx
from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import auth, crud, models, schemas
from .database import Base, engine, get_db


FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
UPLOADS_DIR = Path(__file__).resolve().parents[1] / "uploads"
PROFILE_PHOTOS_DIR = UPLOADS_DIR / "profile-photos"
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


def load_local_env() -> None:
    if not ENV_FILE.is_file():
        return

    for raw_line in ENV_FILE.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


load_local_env()

MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024
MAX_PROFILE_PHOTO_BYTES = 5 * 1024 * 1024
PASSWORD_RESET_TTL_MINUTES = 30
TICKET_ESCALATION_HOURS = int(os.getenv("TICKET_ESCALATION_HOURS", "48"))
APP_ENV = os.getenv("APP_ENV", "development").lower()
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://127.0.0.1:8002")
DEFAULT_ALLOWED_ORIGINS = ",".join(
    {
        FRONTEND_BASE_URL,
        "http://127.0.0.1:8002",
        "http://localhost:8002",
        "null",
    }
)
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS).split(",")
    if origin.strip()
]
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME or "soporte@mediacommerce.net.co")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() not in {"0", "false", "no"}
CACTI_USERNAME = os.getenv("CACTI_USERNAME")
CACTI_PASSWORD = os.getenv("CACTI_PASSWORD")
CACTI_BASE_URL = os.getenv("CACTI_BASE_URL", "").rstrip("/")
ALLOWED_ATTACHMENT_TYPES = {
    "image/gif": ".gif",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

UPLOADS_DIR.mkdir(exist_ok=True)
PROFILE_PHOTOS_DIR.mkdir(exist_ok=True)

Base.metadata.create_all(bind=engine)


def initialize_ticket_sequence() -> None:
    with engine.begin() as connection:
        has_sequence_table = connection.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'"
        ).fetchone() is not None
        if not has_sequence_table:
            return

        result = connection.exec_driver_sql(
            "SELECT seq FROM sqlite_sequence WHERE name = 'tickets'"
        ).fetchone()
        if result is None or result[0] < 999:
            connection.exec_driver_sql(
                "INSERT OR REPLACE INTO sqlite_sequence(name, seq) VALUES ('tickets', 999)"
            )


def migrate_database() -> None:
    initialize_ticket_sequence()
    with engine.begin() as connection:
        columns = connection.exec_driver_sql("PRAGMA table_info(users)").fetchall()
        column_names = {column[1] for column in columns}
        if "password_hash" not in column_names:
            connection.exec_driver_sql("ALTER TABLE users ADD COLUMN password_hash VARCHAR(220)")
        legacy_hash = auth.hash_password("Media2026!")
        connection.exec_driver_sql(
            "UPDATE users SET password_hash = ? WHERE password_hash IS NULL",
            (legacy_hash,),
        )

        ticket_columns = connection.exec_driver_sql("PRAGMA table_info(tickets)").fetchall()
        ticket_column_names = {column[1] for column in ticket_columns}
        if "customer_rating" not in ticket_column_names:
            connection.exec_driver_sql("ALTER TABLE tickets ADD COLUMN customer_rating INTEGER")
        if "customer_rating_comment" not in ticket_column_names:
            connection.exec_driver_sql("ALTER TABLE tickets ADD COLUMN customer_rating_comment TEXT")
        if "customer_rated_at" not in ticket_column_names:
            connection.exec_driver_sql("ALTER TABLE tickets ADD COLUMN customer_rated_at DATETIME")

        attachment_columns = connection.exec_driver_sql("PRAGMA table_info(ticket_attachments)").fetchall()
        attachment_column_names = {column[1] for column in attachment_columns}
        if "comment_id" not in attachment_column_names:
            connection.exec_driver_sql("ALTER TABLE ticket_attachments ADD COLUMN comment_id INTEGER")


migrate_database()

app = FastAPI(
    title="Media Commerce Tickets API",
    version="0.1.0",
    description="Backend para sistema de gestión de tickets.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def validate_choice(value: str, allowed: set, field: str) -> None:
    if value not in allowed:
        options = ", ".join(sorted(allowed))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field} debe ser uno de: {options}",
        )


def ensure_user_exists(db: Session, user_id: int, field: str) -> None:
    if user_id is not None and crud.get_user(db, user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{field} no existe",
        )


def ensure_customer_exists(db: Session, user_id: int) -> None:
    user = crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
    if user.role != "customer":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La gráfica debe asignarse a un usuario cliente",
        )


def send_password_reset_email(email: str, reset_url: str) -> None:
    subject = "Restablecer contraseña - Media Commerce Tickets"
    body = (
        "Hola,\n\n"
        "Recibimos una solicitud para restablecer tu contraseña del sistema de tickets.\n"
        f"Usa este enlace durante los próximos {PASSWORD_RESET_TTL_MINUTES} minutos:\n\n"
        f"{reset_url}\n\n"
        "Si no solicitaste este cambio, puedes ignorar este mensaje."
    )

    if not SMTP_HOST:
        print(f"[password-reset] SMTP no configurado. Enlace para {email}: {reset_url}")
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = SMTP_FROM
    message["To"] = email
    message.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as smtp:
        if SMTP_USE_TLS:
            smtp.starttls()
        if SMTP_USERNAME and SMTP_PASSWORD:
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        smtp.send_message(message)


def get_current_user(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> models.User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Debes iniciar sesión",
        )

    token = authorization.split(" ", 1)[1]
    user_id = auth.decode_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión inválida o expirada",
        )

    user = crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )
    return user


def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden gestionar usuarios",
        )
    return current_user


def require_agent_or_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if current_user.role not in {"admin", "agent"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo agentes o administradores pueden asignar gráficas",
        )
    return current_user


def user_can_access_ticket(ticket: models.Ticket, current_user: models.User) -> bool:
    if current_user.role == "admin":
        return True
    return current_user.id in {ticket.requester_id, ticket.assigned_to_id}


def ensure_ticket_access(ticket: models.Ticket, current_user: models.User) -> None:
    if not user_can_access_ticket(ticket, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este ticket",
        )


def ensure_ticket_management_access(ticket: models.Ticket, current_user: models.User) -> None:
    if current_user.role not in {"admin", "agent"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores y agentes pueden modificar tickets",
        )
    ensure_ticket_access(ticket, current_user)


def require_admin_or_bootstrap(
    payload: schemas.UserCreate,
    authorization: Optional[str],
    db: Session,
) -> None:
    if payload.role == "admin" and crud.count_admins(db) == 0:
        return

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Debes iniciar sesión como administrador",
        )

    user_id = auth.decode_access_token(authorization.split(" ", 1)[1])
    user = crud.get_user(db, user_id) if user_id else None
    if user is None or user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden gestionar usuarios",
        )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/register", response_model=schemas.AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.UserRegister, db: Session = Depends(get_db)):
    role = "admin" if crud.count_admins(db) == 0 else "customer"
    try:
        user = crud.register_user(db, payload, role=role)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo",
        )

    return {"access_token": auth.create_access_token(user.id), "user": user}


@app.post("/auth/login", response_model=schemas.AuthResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, str(payload.email))
    if user is None or not auth.verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
        )

    return {"access_token": auth.create_access_token(user.id), "user": user}


@app.post("/auth/password-reset/request", response_model=schemas.MessageResponse)
def request_password_reset(
    payload: schemas.PasswordResetRequest,
    db: Session = Depends(get_db),
):
    user = crud.get_user_by_email(db, str(payload.email))
    if user is not None:
        token = auth.create_password_reset_token()
        crud.create_password_reset_token(
            db,
            user,
            token,
            ttl_minutes=PASSWORD_RESET_TTL_MINUTES,
        )
        reset_url = f"{FRONTEND_BASE_URL.rstrip('/')}/?reset_token={token}"
        try:
            send_password_reset_email(user.email, reset_url)
        except Exception as error:
            print(f"[password-reset] No se pudo enviar correo a {user.email}: {error}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="No se pudo enviar el correo de recuperación",
            )

    return {
        "message": "Si el correo está registrado, enviaremos instrucciones para restablecer la contraseña."
    }


@app.post("/auth/password-reset/confirm", response_model=schemas.MessageResponse)
def confirm_password_reset(
    payload: schemas.PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    reset_token = crud.get_valid_password_reset_token(db, payload.token)
    if reset_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace de recuperación no es válido o expiró",
        )

    crud.reset_user_password(db, reset_token, payload.password)
    return {"message": "Contraseña actualizada. Ya puedes iniciar sesión."}


@app.get("/auth/me", response_model=schemas.UserRead)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


def build_cacti_image_url(url: str) -> str:
    url = url.strip()
    if url.isdigit() and CACTI_BASE_URL:
        return f"{CACTI_BASE_URL}/graph_image.php?action=draw&local_graph_id={url}"

    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    if parsed.path.endswith("graph_image.php"):
        return url
    if parsed.path.endswith("graphs.php") and query.get("action") == ["graph_edit"] and query.get("id"):
        graph_id = query["id"][0]
        image_path = parsed.path.replace("graphs.php", "graph_image.php")
        return urlunparse(parsed._replace(path=image_path, query="action=draw&local_graph_id=" + graph_id))
    if parsed.path.endswith("graph.php") and query.get("local_graph_id"):
        return urlunparse(parsed._replace(path=parsed.path.replace("graph.php", "graph_image.php"), query="action=draw&local_graph_id=" + query["local_graph_id"][0]))
    if parsed.path.endswith("graph_view.php") and query.get("local_graph_id"):
        return urlunparse(parsed._replace(path=parsed.path.replace("graph_view.php", "graph_image.php"), query="action=draw&local_graph_id=" + query["local_graph_id"][0]))

    return url


async def login_to_cacti(client: httpx.AsyncClient, url: str) -> None:
    parsed = urlparse(url)
    base_path = parsed.path.rsplit("/", 1)[0]
    login_page_url = urlunparse(parsed._replace(path=f"{base_path}/index.php", query=""))
    login_url = login_page_url

    response = await client.get(login_page_url)
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo conectar a Cacti para iniciar sesión",
        )

    token_match = re.search(r'name=["\']?__csrf_magic["\']?[^>]*value=["\']?([^"\']*)', response.text, re.I)
    if not token_match:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se encontró el token CSRF de Cacti",
        )

    data = {
        "__csrf_magic": token_match.group(1),
        "action": "login",
        "login_username": CACTI_USERNAME,
        "login_password": CACTI_PASSWORD,
    }

    response = await client.post(login_url, data=data, headers={"Referer": login_page_url})
    if response.status_code != 200 or "Login to Cacti" in response.text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo iniciar sesión en Cacti. Revisa CACTI_USERNAME y CACTI_PASSWORD.",
        )


@app.get("/client-graphs/{graph_id}/image")
async def proxy_client_graph_image(
    graph_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    graph = crud.get_client_graph(db, graph_id)
    if graph is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gráfica no encontrada")
    if current_user.role == "customer" and graph.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para ver esta gráfica")
    if graph.graph_type != "cacti":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo se pueden obtener imágenes de gráficas Cacti")

    image_url = build_cacti_image_url(str(graph.chart_data).strip())
    parsed = urlparse(image_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL de gráfica inválida")
    if CACTI_BASE_URL:
        allowed = urlparse(CACTI_BASE_URL)
        if parsed.hostname != allowed.hostname:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La URL de Cacti no pertenece al servidor configurado",
            )

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        if CACTI_USERNAME and CACTI_PASSWORD:
            await login_to_cacti(client, image_url)
        response = await client.get(image_url)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No se pudo obtener la imagen de Cacti ({response.status_code})",
        )

    media_type = response.headers.get("content-type", "image/png")
    if not media_type.lower().startswith("image/"):
        if "Login to Cacti" in response.text:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Cacti requiere autenticación. Configura credenciales válidas en backend/.env y reinicia el backend.",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Cacti no devolvió una imagen ({media_type}). Revisa la URL, permisos o credenciales de Cacti.",
        )
    return Response(content=response.content, media_type=media_type)


@app.get("/client-graphs", response_model=list[schemas.ClientGraphRead])
def list_client_graphs(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud.list_client_graphs(db, current_user)


@app.post("/client-graphs", response_model=schemas.ClientGraphRead, status_code=status.HTTP_201_CREATED)
def create_client_graph(
    payload: schemas.ClientGraphCreate,
    current_user: models.User = Depends(require_agent_or_admin),
    db: Session = Depends(get_db),
):
    validate_choice(payload.graph_type, schemas.VALID_GRAPH_TYPES, "graph_type")
    ensure_customer_exists(db, payload.customer_id)
    return crud.create_client_graph(db, payload, assigned_by_id=current_user.id)


@app.patch("/client-graphs/{graph_id}", response_model=schemas.ClientGraphRead)
def update_client_graph(
    graph_id: int,
    payload: schemas.ClientGraphUpdate,
    current_user: models.User = Depends(require_agent_or_admin),
    db: Session = Depends(get_db),
):
    graph = crud.get_client_graph(db, graph_id)
    if graph is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gráfica no encontrada")
    if payload.graph_type:
        validate_choice(payload.graph_type, schemas.VALID_GRAPH_TYPES, "graph_type")
    if payload.customer_id is not None:
        ensure_customer_exists(db, payload.customer_id)
    return crud.update_client_graph(db, graph, payload)


@app.delete("/client-graphs/{graph_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client_graph(
    graph_id: int,
    current_user: models.User = Depends(require_agent_or_admin),
    db: Session = Depends(get_db),
):
    graph = crud.get_client_graph(db, graph_id)
    if graph is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gráfica no encontrada")
    crud.delete_client_graph(db, graph)
    return None


@app.post("/users", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: schemas.UserCreate,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
):
    validate_choice(payload.role, schemas.VALID_ROLES, "role")
    require_admin_or_bootstrap(payload, authorization, db)

    try:
        return crud.create_user(db, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo",
        )


@app.get("/users", response_model=list[schemas.UserRead])
def list_users(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        return [current_user]
    return crud.list_users(db)


@app.patch("/users/{user_id}", response_model=schemas.UserRead)
def update_user(
    user_id: int,
    payload: schemas.UserUpdate,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    if payload.role:
        validate_choice(payload.role, schemas.VALID_ROLES, "role")

    try:
        return crud.update_user(db, user, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo",
        )


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar el usuario administrador activo",
        )

    crud.delete_user(db, user)
    return None


@app.post("/tickets", response_model=schemas.TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: schemas.TicketCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    validate_choice(payload.priority, schemas.VALID_PRIORITIES, "priority")
    default_agent = crud.get_default_agent(db)
    if default_agent is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No hay un agente predeterminado disponible",
        )

    ticket_payload = payload.model_copy(
        update={
            "requester_id": current_user.id,
            "assigned_to_id": default_agent.id,
        }
    )
    return crud.create_ticket(db, ticket_payload)


@app.get("/tickets", response_model=list[schemas.TicketRead])
def list_tickets(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    priority: Optional[str] = None,
    assigned_to_id: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if status_filter:
        validate_choice(status_filter, schemas.VALID_STATUSES, "status")
    if priority:
        validate_choice(priority, schemas.VALID_PRIORITIES, "priority")
    crud.escalate_stale_tickets(db, TICKET_ESCALATION_HOURS, current_user)

    return crud.list_tickets(
        db=db,
        current_user=current_user,
        status=status_filter,
        priority=priority,
        assigned_to_id=assigned_to_id,
        search=search,
        limit=limit,
        offset=offset,
    )


@app.get("/tickets/statistics", response_model=schemas.TicketStatistics)
def get_ticket_statistics(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    crud.escalate_stale_tickets(db, TICKET_ESCALATION_HOURS, current_user)
    return crud.get_ticket_statistics(db, current_user)


@app.get("/tickets/{ticket_id}", response_model=schemas.TicketRead)
def get_ticket(
    ticket_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = crud.get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket no encontrado")
    ensure_ticket_access(ticket, current_user)
    crud.escalate_stale_tickets(db, TICKET_ESCALATION_HOURS, current_user)
    ticket = crud.get_ticket(db, ticket_id)
    return ticket


@app.patch("/tickets/{ticket_id}", response_model=schemas.TicketRead)
def update_ticket(
    ticket_id: int,
    payload: schemas.TicketUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = crud.get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket no encontrado")
    ensure_ticket_management_access(ticket, current_user)

    if payload.status:
        validate_choice(payload.status, schemas.VALID_STATUSES, "status")
    if payload.priority:
        validate_choice(payload.priority, schemas.VALID_PRIORITIES, "priority")
    ensure_user_exists(db, payload.requester_id, "requester_id")
    ensure_user_exists(db, payload.assigned_to_id, "assigned_to_id")

    return crud.update_ticket(db, ticket, payload, actor_id=current_user.id)


@app.post("/tickets/{ticket_id}/rating", response_model=schemas.TicketRead)
def rate_ticket(
    ticket_id: int,
    payload: schemas.TicketRatingCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = crud.get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket no encontrado")
    ensure_ticket_access(ticket, current_user)
    if ticket.requester_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el cliente solicitante puede calificar este ticket",
        )
    if ticket.status not in {"resolved", "closed"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Solo puedes calificar tickets resueltos o cerrados",
        )

    return crud.rate_ticket(db, ticket, payload, actor_id=current_user.id)


@app.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(
    ticket_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = crud.get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket no encontrado")
    ensure_ticket_management_access(ticket, current_user)
    attachment_filenames = [attachment.stored_filename for attachment in ticket.attachments]
    crud.delete_ticket(db, ticket)
    for filename in attachment_filenames:
        path = UPLOADS_DIR / filename
        if path.is_file():
            path.unlink()
    return None


@app.post(
    "/tickets/{ticket_id}/comments",
    response_model=schemas.TicketCommentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    ticket_id: int,
    payload: schemas.TicketCommentCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = crud.get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket no encontrado")
    ensure_ticket_access(ticket, current_user)
    comment_payload = payload.model_copy(update={"author_id": current_user.id})
    return crud.create_comment(db, ticket_id, comment_payload)


@app.get("/tickets/{ticket_id}/comments", response_model=list[schemas.TicketCommentRead])
def list_comments(
    ticket_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = crud.get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket no encontrado")
    ensure_ticket_access(ticket, current_user)
    return crud.list_comments(db, ticket_id)


@app.get("/tickets/{ticket_id}/events", response_model=list[schemas.TicketEventRead])
def list_ticket_events(
    ticket_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = crud.get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket no encontrado")
    ensure_ticket_access(ticket, current_user)
    return crud.list_ticket_events(db, ticket_id)


@app.post(
    "/tickets/{ticket_id}/attachments",
    response_model=schemas.TicketAttachmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_ticket_attachment(
    ticket_id: int,
    comment_id: Optional[int] = None,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ticket = crud.get_ticket(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket no encontrado")
    ensure_ticket_access(ticket, current_user)
    if comment_id is not None:
        comment = crud.get_comment(db, comment_id)
        if comment is None or comment.ticket_id != ticket_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comentario no encontrado")

    extension = ALLOWED_ATTACHMENT_TYPES.get(file.content_type or "")
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Solo se permiten capturas en formato PNG, JPG, GIF o WebP",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La captura está vacía",
        )
    if len(content) > MAX_ATTACHMENT_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="La captura no puede superar 5 MB",
        )

    original_filename = Path(file.filename or "captura").name
    stored_filename = f"{uuid4().hex}{extension}"
    destination = UPLOADS_DIR / stored_filename
    destination.write_bytes(content)

    return crud.create_attachment(
        db=db,
        ticket_id=ticket_id,
        comment_id=comment_id,
        uploaded_by_id=current_user.id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
        url=f"/uploads/{stored_filename}",
    )


# ==================== USER PROFILE ENDPOINTS ====================

@app.get("/profile-photos/{stored_filename}", include_in_schema=False)
def get_profile_photo_file(stored_filename: str):
    filename = Path(stored_filename).name
    path = PROFILE_PHOTOS_DIR / filename
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto no encontrada")

    extension = path.suffix.lower()
    media_type = {
        ".gif": "image/gif",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(extension, "application/octet-stream")

    return FileResponse(path, media_type=media_type)


@app.post("/api/profile/photo", response_model=schemas.UserProfileRead, include_in_schema=False)
@app.post("/profile/photo", response_model=schemas.UserProfileRead)
async def upload_my_profile_photo(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    extension = ALLOWED_ATTACHMENT_TYPES.get(file.content_type or "")
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Solo se permiten fotos en formato PNG, JPG, GIF o WebP",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La foto está vacía",
        )
    if len(content) > MAX_PROFILE_PHOTO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="La foto no puede superar 5 MB",
        )

    profile = crud.get_or_create_user_profile(db, current_user.id)
    previous_filename = None
    if profile.photo_url and profile.photo_url.startswith("/profile-photos/"):
        previous_filename = Path(profile.photo_url).name

    stored_filename = f"user_{current_user.id}_{uuid4().hex}{extension}"
    destination = PROFILE_PHOTOS_DIR / stored_filename
    destination.write_bytes(content)

    updated_profile = crud.update_user_profile(
        db,
        profile,
        schemas.UserProfileUpdate(photo_url=f"/profile-photos/{stored_filename}"),
    )

    if previous_filename and previous_filename != stored_filename:
        previous_path = PROFILE_PHOTOS_DIR / previous_filename
        if previous_path.is_file():
            previous_path.unlink()

    return updated_profile


@app.get("/api/profile", response_model=schemas.UserProfileRead, include_in_schema=False)
@app.get("/profile", response_model=schemas.UserProfileRead)
def get_my_profile(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener mi perfil de usuario."""
    profile = crud.get_or_create_user_profile(db, current_user.id)
    return profile


@app.put("/api/profile", response_model=schemas.UserProfileRead, include_in_schema=False)
@app.put("/profile", response_model=schemas.UserProfileRead)
def update_my_profile(
    payload: schemas.UserProfileUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualizar mi perfil de usuario."""
    profile = crud.get_or_create_user_profile(db, current_user.id)
    updated_profile = crud.update_user_profile(db, profile, payload)
    return updated_profile


@app.get("/api/users/{user_id}/profile", response_model=schemas.UserProfileRead, include_in_schema=False)
@app.get("/users/{user_id}/profile", response_model=schemas.UserProfileRead)
def get_user_profile(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Obtener el perfil de otro usuario (solo admin puede ver perfiles de otros)."""
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver el perfil de otro usuario",
        )

    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    profile = crud.get_or_create_user_profile(db, user_id)
    return profile


@app.get("/uploads/{stored_filename}", include_in_schema=False)
def get_ticket_attachment_file(
    stored_filename: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    attachment = crud.get_attachment_by_stored_filename(db, Path(stored_filename).name)
    if attachment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adjunto no encontrado")
    ensure_ticket_access(attachment.ticket, current_user)

    path = UPLOADS_DIR / attachment.stored_filename
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado")

    return FileResponse(
        path,
        media_type=attachment.content_type,
        filename=attachment.original_filename,
    )


@app.get("/", include_in_schema=False)
def frontend_index():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend")
