# Backend de Tickets - Media Commerce

API en Python para gestionar tickets de soporte.

## Ejecutar

Desde la carpeta `backend`:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export TICKETS_SECRET_KEY="cambia-este-secreto-local"
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

Desde la raíz del proyecto, usa el módulo completo:

```bash
backend/.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8002
```

La documentación queda disponible en:

- `http://127.0.0.1:8002/docs`
- `http://127.0.0.1:8002/redoc`

## Endpoints principales

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/password-reset/request`
- `POST /auth/password-reset/confirm`
- `GET /auth/me`
- `POST /users`
- `GET /users`
- `PATCH /users/{user_id}`
- `DELETE /users/{user_id}`
- `GET /client-graphs`
- `POST /client-graphs`
- `PATCH /client-graphs/{graph_id}`
- `DELETE /client-graphs/{graph_id}`
- `POST /tickets`
- `GET /tickets`
- `GET /tickets/{ticket_id}`
- `PATCH /tickets/{ticket_id}`
- `POST /tickets/{ticket_id}/rating`
- `DELETE /tickets/{ticket_id}`
- `POST /tickets/{ticket_id}/comments`
- `GET /tickets/{ticket_id}/comments`

La base de datos SQLite se crea automáticamente en `backend/tickets.db`.

## Autenticación

Los usuarios nuevos se registran con correo y contraseña en `/auth/register`.
El primer usuario registrado queda como administrador inicial; los siguientes quedan como clientes.

Las operaciones protegidas usan:

```http
Authorization: Bearer <token>
```

Los usuarios antiguos sin contraseña reciben temporalmente la clave `Media2026!`.
Después de ingresar, un administrador puede cambiarla desde la pantalla Usuarios.

En producción configura `APP_ENV=production` y un `TICKETS_SECRET_KEY` fuerte. El backend no arranca en producción con el secreto local por defecto.

Para restringir CORS a dominios específicos, usa:

```bash
export ALLOWED_ORIGINS="https://tickets.tudominio.com,https://soporte.tudominio.com"
```

## Arranque automatico en Ubuntu

Para dejar el backend como servicio y que arranque automaticamente al reiniciar el servidor, usa la guia:

```bash
../deploy/UBUNTU_BACKEND_SYSTEMD.md
```

## Ciclo de vida de tickets

Los tickets manejan estos estados: `open`, `in_progress`, `waiting_customer`, `resolved`, `escalated` y `closed`.

- Al crear un ticket queda en `open`.
- Si un agente o administrador comenta un ticket no cerrado, cambia a `resolved`.
- Si un cliente responde un ticket no cerrado, vuelve a `open`.
- Si un ticket queda sin resolución durante el tiempo configurado, cambia a `escalated`.
- El cierre se hace cuando un agente o administrador establece el estado `closed` después de confirmar la resolución.
- El cliente solicitante puede calificar un ticket con una nota de 1 a 5 cuando esté `resolved` o `closed`.

El umbral de escalamiento se configura con:

```bash
export TICKET_ESCALATION_HOURS="48"
```

## Recuperación de contraseña por correo

El formulario "¿Olvidaste tu contraseña?" envía un enlace al correo registrado del usuario. Para enviar correos reales, configura estas variables antes de iniciar `uvicorn`:

```bash
export FRONTEND_BASE_URL="http://127.0.0.1:8002"
export SMTP_HOST="smtp.tudominio.com"
export SMTP_PORT="587"
export SMTP_USERNAME="usuario-smtp"
export SMTP_PASSWORD="clave-smtp"
export SMTP_FROM="soporte@mediacommerce.net.co"
export SMTP_USE_TLS="true"
```

Si `SMTP_HOST` no está configurado, el backend imprime el enlace de recuperación en la consola para pruebas locales.

## Integración con Cacti

Para mostrar gráficas Cacti en el sistema sin redireccionar, configura estas variables antes de iniciar el backend:

```bash
cp .env.example .env
```

Luego edita `backend/.env` con el usuario, contraseña y URL base reales de Cacti:

```bash
CACTI_BASE_URL="http://45.184.225.4/cacti"
CACTI_USERNAME="usuario-cacti"
CACTI_PASSWORD="clave-cacti"
```

Las gráficas almacenadas como `graph_type: cacti` se cargarán a través del proxy del backend y usarán estas credenciales si están disponibles. En el campo de datos puedes guardar una URL completa de Cacti o solo el `local_graph_id` cuando `CACTI_BASE_URL` esté configurado. Si configuras `CACTI_BASE_URL`, el backend solo aceptará imágenes del mismo host para evitar solicitudes a destinos no autorizados.
