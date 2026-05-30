# Arranque automatico del backend en Ubuntu

Esta configuracion deja el backend como servicio de `systemd`, para que arranque al iniciar el servidor y se reinicie si el proceso falla.

Los comandos asumen que el proyecto queda en:

```bash
/opt/tickets
```

Si usas otra ruta, cambia `/opt/tickets` en `deploy/systemd/tickets-backend.service`.

## 1. Preparar el servidor

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip rsync
id tickets >/dev/null 2>&1 || sudo useradd --system --home /opt/tickets --shell /usr/sbin/nologin tickets
sudo mkdir -p /opt/tickets
```

Si necesitas ajustar permisos manualmente despues de transferir:

```bash
sudo chown -R tickets:tickets /opt/tickets
```

## 2. Transferir el proyecto al servidor

Desde tu equipo local, en la raiz del proyecto:

```bash
./deploy/deploy_to_ubuntu.sh usuario@IP_DEL_SERVIDOR /opt/tickets
```

Ejemplo:

```bash
./deploy/deploy_to_ubuntu.sh ubuntu@203.0.113.10 /opt/tickets
```

El script no sube `.venv`, `backend/.env`, bases de datos SQLite ni `backend/uploads`, para no pisar datos o secretos de produccion.

## 3. Crear el entorno Python

```bash
cd /opt/tickets/backend
sudo -u tickets python3 -m venv .venv
sudo -u tickets /opt/tickets/backend/.venv/bin/pip install -r requirements.txt
```

## 4. Configurar variables de entorno

Crea `/opt/tickets/backend/.env`:

```bash
APP_ENV=production
TICKETS_SECRET_KEY=pon_aqui_una_clave_larga_y_unica
FRONTEND_BASE_URL=http://127.0.0.1:8002
ALLOWED_ORIGINS=http://127.0.0.1:8002
TICKET_ESCALATION_HOURS=48
```

Puedes generar una clave segura con:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Si vas a usar dominio y Nginx, cambia `FRONTEND_BASE_URL` y `ALLOWED_ORIGINS` por tu dominio, por ejemplo:

```bash
FRONTEND_BASE_URL=https://tickets.tudominio.com
ALLOWED_ORIGINS=https://tickets.tudominio.com
```

## 5. Instalar y activar el servicio

```bash
sudo cp /opt/tickets/deploy/systemd/tickets-backend.service /etc/systemd/system/tickets-backend.service
sudo systemctl daemon-reload
sudo systemctl enable tickets-backend
sudo systemctl start tickets-backend
```

Con `enable`, Ubuntu lo vuelve a levantar automaticamente despues de apagar o reiniciar el servidor.

## 6. Verificar

```bash
sudo systemctl status tickets-backend --no-pager
curl http://127.0.0.1:8002/health
```

Ver logs en vivo:

```bash
sudo journalctl -u tickets-backend -f
```

Reiniciar despues de cambios:

```bash
sudo systemctl restart tickets-backend
```

## Nota sobre acceso publico

El servicio escucha en `127.0.0.1:8002`, pensado para publicarlo con Nginx como proxy inverso.

Si quieres exponerlo directamente sin Nginx, cambia en el archivo `.service`:

```ini
--host 127.0.0.1
```

por:

```ini
--host 0.0.0.0
```

y luego ejecuta:

```bash
sudo systemctl daemon-reload
sudo systemctl restart tickets-backend
```
