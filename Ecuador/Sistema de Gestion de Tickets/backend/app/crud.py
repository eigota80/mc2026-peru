from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from . import auth
from . import models, schemas


def normalize_email(email: str) -> str:
    return str(email).strip().lower()


def create_user(db: Session, payload: schemas.UserCreate) -> models.User:
    data = payload.model_dump()
    password = data.pop("password")
    data["email"] = normalize_email(data["email"])
    user = models.User(**data, password_hash=auth.hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def register_user(db: Session, payload: schemas.UserRegister, role: str = "customer") -> models.User:
    user = models.User(
        name=payload.name,
        email=normalize_email(payload.email),
        role=role,
        password_hash=auth.hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return (
        db.query(models.User)
        .options(joinedload(models.User.profile))
        .filter(models.User.id == user_id)
        .first()
    )


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return (
        db.query(models.User)
        .options(joinedload(models.User.profile))
        .filter(models.User.email == normalize_email(email))
        .first()
    )


def list_users(db: Session):
    return db.query(models.User).options(joinedload(models.User.profile)).order_by(models.User.name).all()


def count_users(db: Session) -> int:
    return db.query(models.User).count()


def count_admins(db: Session) -> int:
    return db.query(models.User).filter(models.User.role == "admin").count()


def get_default_agent(db: Session) -> Optional[models.User]:
    agent = (
        db.query(models.User)
        .filter(models.User.role == "agent")
        .order_by(models.User.id.asc())
        .first()
    )
    if agent:
        return agent

    return (
        db.query(models.User)
        .filter(models.User.role == "admin")
        .order_by(models.User.id.asc())
        .first()
    )


def update_user(
    db: Session,
    user: models.User,
    payload: schemas.UserUpdate,
) -> models.User:
    data = payload.model_dump(exclude_unset=True)
    password = data.pop("password", None)
    if "email" in data:
        data["email"] = normalize_email(data["email"])

    for field, value in data.items():
        setattr(user, field, value)
    if password:
        user.password_hash = auth.hash_password(password)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: models.User) -> None:
    db.query(models.ClientGraph).filter(models.ClientGraph.customer_id == user.id).delete()
    db.query(models.ClientGraph).filter(models.ClientGraph.assigned_by_id == user.id).update(
        {"assigned_by_id": None}
    )
    db.query(models.Ticket).filter(models.Ticket.requester_id == user.id).update(
        {"requester_id": None}
    )
    db.query(models.Ticket).filter(models.Ticket.assigned_to_id == user.id).update(
        {"assigned_to_id": None}
    )
    db.query(models.TicketComment).filter(models.TicketComment.author_id == user.id).update(
        {"author_id": None}
    )
    db.query(models.TicketAttachment).filter(models.TicketAttachment.uploaded_by_id == user.id).update(
        {"uploaded_by_id": None}
    )
    db.query(models.TicketEvent).filter(models.TicketEvent.actor_id == user.id).update(
        {"actor_id": None}
    )
    db.delete(user)
    db.commit()


def create_password_reset_token(
    db: Session,
    user: models.User,
    token: str,
    ttl_minutes: int = 30,
) -> models.PasswordResetToken:
    reset_token = models.PasswordResetToken(
        user_id=user.id,
        token_hash=auth.hash_password_reset_token(token),
        expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes),
    )
    db.add(reset_token)
    db.commit()
    db.refresh(reset_token)
    return reset_token


def get_valid_password_reset_token(
    db: Session,
    token: str,
) -> Optional[models.PasswordResetToken]:
    token_hash = auth.hash_password_reset_token(token)
    return (
        db.query(models.PasswordResetToken)
        .filter(
            models.PasswordResetToken.token_hash == token_hash,
            models.PasswordResetToken.used_at.is_(None),
            models.PasswordResetToken.expires_at > datetime.utcnow(),
        )
        .first()
    )


def reset_user_password(
    db: Session,
    reset_token: models.PasswordResetToken,
    password: str,
) -> models.User:
    user = reset_token.user
    user.password_hash = auth.hash_password(password)
    reset_token.used_at = datetime.utcnow()
    db.add(user)
    db.add(reset_token)
    db.commit()
    db.refresh(user)
    return user


def create_client_graph(
    db: Session,
    payload: schemas.ClientGraphCreate,
    assigned_by_id: int,
) -> models.ClientGraph:
    graph = models.ClientGraph(**payload.model_dump(), assigned_by_id=assigned_by_id)
    db.add(graph)
    db.commit()
    db.refresh(graph)
    return get_client_graph(db, graph.id)


def get_client_graph(db: Session, graph_id: int) -> Optional[models.ClientGraph]:
    return (
        db.query(models.ClientGraph)
        .options(
            joinedload(models.ClientGraph.customer),
            joinedload(models.ClientGraph.assigned_by),
        )
        .filter(models.ClientGraph.id == graph_id)
        .first()
    )


def list_client_graphs(db: Session, current_user: models.User):
    query = db.query(models.ClientGraph).options(
        joinedload(models.ClientGraph.customer),
        joinedload(models.ClientGraph.assigned_by),
    )
    if current_user.role == "customer":
        query = query.filter(models.ClientGraph.customer_id == current_user.id)
    return query.order_by(models.ClientGraph.updated_at.desc()).all()


def update_client_graph(
    db: Session,
    graph: models.ClientGraph,
    payload: schemas.ClientGraphUpdate,
) -> models.ClientGraph:
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(graph, field, value)
    db.add(graph)
    db.commit()
    db.refresh(graph)
    return get_client_graph(db, graph.id)


def delete_client_graph(db: Session, graph: models.ClientGraph) -> None:
    db.delete(graph)
    db.commit()


def create_ticket(db: Session, payload: schemas.TicketCreate) -> models.Ticket:
    max_ticket_id = db.query(func.max(models.Ticket.id)).scalar() or 0
    next_ticket_id = max(max_ticket_id, 999) + 1
    ticket = models.Ticket(id=next_ticket_id, **payload.model_dump())
    db.add(ticket)
    db.flush()
    db.add(
        models.TicketEvent(
            ticket_id=ticket.id,
            actor_id=ticket.requester_id,
            event_type="created",
            message="Ticket creado",
        )
    )
    db.add(
        models.TicketEvent(
            ticket_id=ticket.id,
            actor_id=ticket.requester_id,
            event_type="status_changed",
            message="Estado inicial",
            field_name="status",
            old_value=None,
            new_value=ticket.status,
        )
    )
    db.commit()
    db.refresh(ticket)
    return get_ticket(db, ticket.id)


def get_ticket(db: Session, ticket_id: int) -> Optional[models.Ticket]:
    return (
        db.query(models.Ticket)
        .options(
            joinedload(models.Ticket.requester).joinedload(models.User.profile),
            joinedload(models.Ticket.assignee).joinedload(models.User.profile),
            joinedload(models.Ticket.comments)
            .joinedload(models.TicketComment.author)
            .joinedload(models.User.profile),
            joinedload(models.Ticket.comments)
            .joinedload(models.TicketComment.attachments)
            .joinedload(models.TicketAttachment.uploader)
            .joinedload(models.User.profile),
            joinedload(models.Ticket.attachments)
            .joinedload(models.TicketAttachment.uploader)
            .joinedload(models.User.profile),
            joinedload(models.Ticket.events)
            .joinedload(models.TicketEvent.actor)
            .joinedload(models.User.profile),
        )
        .filter(models.Ticket.id == ticket_id)
        .first()
    )


def list_tickets(
    db: Session,
    current_user: Optional[models.User] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to_id: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    query = db.query(models.Ticket).options(
        joinedload(models.Ticket.requester).joinedload(models.User.profile),
        joinedload(models.Ticket.assignee).joinedload(models.User.profile),
        joinedload(models.Ticket.attachments),
    )

    # Filtrar por usuario actual si no es admin
    if current_user and current_user.role != "admin":
        query = query.filter(
            or_(
                models.Ticket.requester_id == current_user.id,
                models.Ticket.assigned_to_id == current_user.id,
            )
        )

    if status:
        query = query.filter(models.Ticket.status == status)
    if priority:
        query = query.filter(models.Ticket.priority == priority)
    if assigned_to_id:
        query = query.filter(models.Ticket.assigned_to_id == assigned_to_id)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                models.Ticket.title.ilike(pattern),
                models.Ticket.description.ilike(pattern),
                models.Ticket.category.ilike(pattern),
            )
        )

    return (
        query.order_by(models.Ticket.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def update_ticket(
    db: Session,
    ticket: models.Ticket,
    payload: schemas.TicketUpdate,
    actor_id: Optional[int] = None,
) -> models.Ticket:
    data = payload.model_dump(exclude_unset=True)
    tracked_labels = {
        "title": "título",
        "description": "descripción",
        "status": "estado",
        "priority": "prioridad",
        "category": "categoría",
        "requester_id": "solicitante",
        "assigned_to_id": "responsable",
    }
    events = []

    for field, value in data.items():
        old_value = getattr(ticket, field)
        if old_value != value:
            label = tracked_labels.get(field, field)
            events.append(
                models.TicketEvent(
                    ticket_id=ticket.id,
                    actor_id=actor_id,
                    event_type="status_changed" if field == "status" else "updated",
                    message="Cambió estado" if field == "status" else f"Cambió {label}",
                    field_name=field,
                    old_value=str(old_value) if old_value is not None else None,
                    new_value=str(value) if value is not None else None,
                )
            )
        setattr(ticket, field, value)

    if data.get("status") == "closed" and ticket.closed_at is None:
        ticket.closed_at = datetime.utcnow()
    if data.get("status") and data.get("status") != "closed":
        ticket.closed_at = None

    db.add(ticket)
    db.add_all(events)
    db.commit()
    db.refresh(ticket)
    return get_ticket(db, ticket.id)


def rate_ticket(
    db: Session,
    ticket: models.Ticket,
    payload: schemas.TicketRatingCreate,
    actor_id: Optional[int] = None,
) -> models.Ticket:
    old_rating = ticket.customer_rating
    ticket.customer_rating = payload.rating
    ticket.customer_rating_comment = payload.comment
    ticket.customer_rated_at = datetime.utcnow()
    db.add(ticket)
    db.add(
        models.TicketEvent(
            ticket_id=ticket.id,
            actor_id=actor_id,
            event_type="rated",
            message="Cliente calificó el ticket",
            field_name="customer_rating",
            old_value=str(old_rating) if old_rating is not None else None,
            new_value=str(payload.rating),
        )
    )
    db.commit()
    db.refresh(ticket)
    return get_ticket(db, ticket.id)


def delete_ticket(db: Session, ticket: models.Ticket) -> None:
    db.delete(ticket)
    db.commit()


def create_comment(
    db: Session,
    ticket_id: int,
    payload: schemas.TicketCommentCreate,
) -> models.TicketComment:
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    actor = get_user(db, payload.author_id) if payload.author_id else None
    comment = models.TicketComment(ticket_id=ticket_id, **payload.model_dump())
    db.add(comment)
    db.flush()
    db.add(
        models.TicketEvent(
            ticket_id=ticket_id,
            actor_id=payload.author_id,
            event_type="commented",
            message="Agregó un comentario",
        )
    )
    if ticket is not None and actor is not None and ticket.status != "closed":
        next_status = "resolved" if actor.role in {"admin", "agent"} else "open"
        if ticket.status != next_status:
            old_status = ticket.status
            ticket.status = next_status
            ticket.closed_at = None
            db.add(ticket)
            db.add(
                models.TicketEvent(
                    ticket_id=ticket_id,
                    actor_id=payload.author_id,
                    event_type="status_changed",
                    message="Cambió estado por respuesta",
                    field_name="status",
                    old_value=old_status,
                    new_value=next_status,
                )
            )
    db.commit()
    db.refresh(comment)
    return comment


def escalate_stale_tickets(
    db: Session,
    escalation_hours: int,
    current_user: Optional[models.User] = None,
) -> int:
    if escalation_hours <= 0:
        return 0

    cutoff = datetime.utcnow() - timedelta(hours=escalation_hours)
    query = db.query(models.Ticket).filter(
        models.Ticket.status.in_(("open", "in_progress", "waiting_customer")),
        models.Ticket.updated_at <= cutoff,
    )
    if current_user and current_user.role != "admin":
        query = query.filter(
            or_(
                models.Ticket.requester_id == current_user.id,
                models.Ticket.assigned_to_id == current_user.id,
            )
        )

    escalated = query.all()
    for ticket in escalated:
        old_status = ticket.status
        ticket.status = "escalated"
        db.add(ticket)
        db.add(
            models.TicketEvent(
                ticket_id=ticket.id,
                actor_id=None,
                event_type="status_changed",
                message=f"Escalado automáticamente tras {escalation_hours} horas sin resolución",
                field_name="status",
                old_value=old_status,
                new_value="escalated",
            )
        )

    if escalated:
        db.commit()
    return len(escalated)


def list_comments(db: Session, ticket_id: int):
    return (
        db.query(models.TicketComment)
        .options(
            joinedload(models.TicketComment.author).joinedload(models.User.profile),
            joinedload(models.TicketComment.attachments)
            .joinedload(models.TicketAttachment.uploader)
            .joinedload(models.User.profile),
        )
        .filter(models.TicketComment.ticket_id == ticket_id)
        .order_by(models.TicketComment.created_at.asc())
        .all()
    )


def create_attachment(
    db: Session,
    ticket_id: int,
    comment_id: Optional[int],
    uploaded_by_id: int,
    original_filename: str,
    stored_filename: str,
    content_type: str,
    size_bytes: int,
    url: str,
) -> models.TicketAttachment:
    attachment = models.TicketAttachment(
        ticket_id=ticket_id,
        comment_id=comment_id,
        uploaded_by_id=uploaded_by_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        content_type=content_type,
        size_bytes=size_bytes,
        url=url,
    )
    db.add(attachment)
    db.flush()
    db.add(
        models.TicketEvent(
            ticket_id=ticket_id,
            actor_id=uploaded_by_id,
            event_type="attached",
            message=f"Adjuntó imagen: {original_filename}",
            field_name="attachment",
            new_value=original_filename,
        )
    )
    db.commit()
    db.refresh(attachment)
    return attachment


def get_comment(db: Session, comment_id: int) -> Optional[models.TicketComment]:
    return db.query(models.TicketComment).filter(models.TicketComment.id == comment_id).first()


def get_attachment_by_stored_filename(
    db: Session,
    stored_filename: str,
) -> Optional[models.TicketAttachment]:
    return (
        db.query(models.TicketAttachment)
        .options(joinedload(models.TicketAttachment.ticket))
        .filter(models.TicketAttachment.stored_filename == stored_filename)
        .first()
    )


def list_ticket_events(db: Session, ticket_id: int):
    return (
        db.query(models.TicketEvent)
        .options(joinedload(models.TicketEvent.actor).joinedload(models.User.profile))
        .filter(models.TicketEvent.ticket_id == ticket_id)
        .order_by(models.TicketEvent.created_at.asc())
        .all()
    )


def get_ticket_statistics(db: Session, current_user: Optional[models.User] = None) -> schemas.TicketStatistics:
    # Base query
    query = db.query(models.Ticket)

    # Filtrar por usuario actual si no es admin
    if current_user and current_user.role != "admin":
        query = query.filter(
            or_(
                models.Ticket.requester_id == current_user.id,
                models.Ticket.assigned_to_id == current_user.id,
            )
        )

    total = query.count()

    # By status
    by_status = {}
    for status in schemas.VALID_STATUSES:
        count = query.filter(models.Ticket.status == status).count()
        by_status[status] = count

    # By priority
    by_priority = {}
    for priority in schemas.VALID_PRIORITIES:
        count = query.filter(models.Ticket.priority == priority).count()
        by_priority[priority] = count

    # By category
    categories = query.with_entities(models.Ticket.category).distinct().all()
    by_category = {}
    for (category,) in categories:
        count = query.filter(models.Ticket.category == category).count()
        by_category[category] = count

    # By assignee
    assignees = query.with_entities(models.Ticket.assigned_to_id, models.User.name).join(
        models.User, models.Ticket.assigned_to_id == models.User.id, isouter=True
    ).filter(models.Ticket.assigned_to_id.isnot(None)).distinct().all()
    by_assignee = {}
    for user_id, user_name in assignees:
        count = query.filter(models.Ticket.assigned_to_id == user_id).count()
        by_assignee[user_name or f"Usuario {user_id}"] = count

    rated_query = query.filter(models.Ticket.customer_rating.isnot(None))
    ratings_total = rated_query.count()
    happy_total = rated_query.filter(models.Ticket.customer_rating >= 4).count()
    happy_percentage = round((happy_total / ratings_total) * 100) if ratings_total else 0
    negative_tickets = (
        rated_query
        .options(joinedload(models.Ticket.requester))
        .filter(models.Ticket.customer_rating < 4)
        .order_by(models.Ticket.customer_rated_at.desc())
        .limit(25)
        .all()
    )
    negative_ratings = [
        {
            "ticket_id": ticket.id,
            "ticket_title": ticket.title,
            "customer_name": ticket.requester.name if ticket.requester else "Cliente sin asignar",
            "rating": ticket.customer_rating,
            "comment": ticket.customer_rating_comment,
            "rated_at": ticket.customer_rated_at,
        }
        for ticket in negative_tickets
    ]

    return schemas.TicketStatistics(
        total=total,
        by_status=by_status,
        by_priority=by_priority,
        by_category=by_category,
        by_assignee=by_assignee,
        ratings_total=ratings_total,
        happy_percentage=happy_percentage,
        negative_ratings=negative_ratings,
    )


# ==================== USER PROFILE CRUD ====================

def create_user_profile(
    db: Session,
    user_id: int,
    payload: schemas.UserProfileCreate,
) -> models.UserProfile:
    """Crear un perfil de usuario."""
    profile = models.UserProfile(user_id=user_id, **payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def get_user_profile(db: Session, user_id: int) -> Optional[models.UserProfile]:
    """Obtener el perfil de un usuario."""
    return db.query(models.UserProfile).filter(models.UserProfile.user_id == user_id).first()


def update_user_profile(
    db: Session,
    profile: models.UserProfile,
    payload: schemas.UserProfileUpdate,
) -> models.UserProfile:
    """Actualizar el perfil de un usuario."""
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(profile, field, value)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def delete_user_profile(db: Session, profile: models.UserProfile) -> None:
    """Eliminar el perfil de un usuario."""
    db.delete(profile)
    db.commit()


def get_or_create_user_profile(
    db: Session,
    user_id: int,
) -> models.UserProfile:
    """Obtener o crear el perfil de un usuario con valores por defecto."""
    profile = get_user_profile(db, user_id)
    if not profile:
        profile = create_user_profile(
            db,
            user_id,
            schemas.UserProfileCreate(),
        )
    return profile
