# MCP Web Connector — Media Commerce Peru

Servidor MCP local por `stdio` para conectarse al hosting web y a la base MariaDB `bdmcperu` por SSH.

> **Regla de oro:** Todo acceso al servidor remoto o a la base de datos DEBE pasar por este conector MCP.
> Prohibido: SSH directo, SCP, clientes de BD externos, curl/wget de escritura.

---

## Estado del servidor (actualizado 2026-05-29)

| Parametro | Valor |
|---|---|
| Host | `179.43.82.54` (CentOS 7, Linux 3.10.0) |
| Usuario SSH operacional | `mcp-agent` |
| Autenticacion SSH | Solo RSA 4096 — llave en `mcp_web_connector/id_rsa` |
| Passphrase de la llave | En `.env` como `MCP_WEB_SSH_KEY_PASSPHRASE` (no en git) |
| Fingerprint servidor | `SHA256:GCxkhUI4ysNw9LJEayIFdF2BJjWRRrdZp51mVi/syBw` |
| PHP | 7.4.19 |
| Usuario BD activo | `root` (temporal — ver pendientes) |
| BD | `bdmcperu` — 69 tablas (WordPress + tablas custom) |
| Estado MCP | **Operativo** — `config_summary` y consultas BD OK |

### Scripts completados
- `01-setup-mcp-agent-user.sh` — usuario mcp-agent creado
- `07-install-rsa-public-key.sh` — clave RSA instalada en authorized_keys
- `04-harden-sshd.sh` — SSH hardening aplicado

### Pendiente
- `03-setup-db-user.sh` — crear usuario `mcp_agent_ro` (SELECT only) y reemplazar `root`
- `05-setup-staging.sh` — entorno de staging en puerto 8080

---

## Inicio rapido para cualquier agente

### 1. Verificar que el MCP responde

```bash
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}\n{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"config_summary","arguments":{}}}\n' \
  | /RUTA/mcp_web_connector/.venv/bin/python /RUTA/mcp_web_connector/server.py 2>/dev/null
```

Debe responder con el resumen de configuracion (sin credenciales).

### 2. Verificacion obligatoria antes de cualquier tarea

Ejecutar `config_summary`. Si falla, detener y reportar. No continuar sin MCP operativo.

### 3. Skills disponibles via Claude Code

Una vez el MCP esta cargado en `~/.claude/settings.json`, Claude Code expone estas herramientas:

| Skill | Descripcion |
|---|---|
| `config_summary` | Verifica que el agente cargo bien la config |
| `ssh_health` | Diagrama conectividad SSH y versiones del servidor |
| `remote_list` | Lista archivos en directorio remoto |
| `remote_read_text` | Lee archivo remoto (limite 100 000 bytes) |
| `mysql_query_readonly` | SELECT / SHOW / DESCRIBE / EXPLAIN en bdmcperu |
| `mysql_list_tables` | Lista tablas de la BD |
| `mysql_describe_table` | Columnas de una tabla |
| `wordpress_users` | Busca usuarios en wp_users |
| `find_client_columns` | Detecta columnas de clientes/RUC/contacto |
| `export_result_json` | Ejecuta SELECT y devuelve JSON |

### 4. Configuracion en settings.json de Claude Code

```json
{
  "mcpServers": {
    "mcperu-web": {
      "command": "/RUTA_ABSOLUTA/mcp_web_connector/.venv/bin/python",
      "args": ["/RUTA_ABSOLUTA/mcp_web_connector/server.py"],
      "env": {
        "MCP_WEB_SSH_HOST": "179.43.82.54",
        "MCP_WEB_SSH_PORT": "22",
        "MCP_WEB_SSH_USER": "mcp-agent",
        "MCP_WEB_SSH_KEY_FILE": "/RUTA_ABSOLUTA/mcp_web_connector/id_rsa",
        "MCP_WEB_DB_HOST": "127.0.0.1",
        "MCP_WEB_DB_PORT": "3306",
        "MCP_WEB_DB_NAME": "bdmcperu",
        "MCP_WEB_DB_USER": "root"
      }
    }
  }
}
```

> `MCP_WEB_SSH_KEY_PASSPHRASE` y `MCP_WEB_DB_PASSWORD` se leen del `.env` local — no incluirlos en settings.json.

---

## Problema conocido y solucion (2026-05-29)

**Error:** `AttributeError: module 'paramiko' has no attribute 'DSSKey'`

**Causa:** paramiko 5.x elimino la clase `DSSKey`; sshtunnel 0.4.0 la referencia al importar.

**Solucion aplicada en `server.py`:** stub de compatibilidad insertado antes del `import sshtunnel`. No requiere downgrade ni actualizacion de dependencias.

---

---

## Indice

1. [Herramientas disponibles](#herramientas-disponibles)
2. [Instalacion del conector](#instalacion)
3. [Configuracion MCP](#configuracion-mcp)
4. [Seguridad del conector](#seguridad)
5. [Usuario mcp-agent en el servidor](#usuario-mcp-agent-en-el-servidor)
6. [WebOps Agent — Flujo de deploy](#webops-agent--flujo-de-deploy)
7. [Estrategia de rollback](#estrategia-de-rollback)

---

## Herramientas disponibles

### Lectura (activas)

| Herramienta | Descripcion |
|---|---|
| `ssh_health` | Verifica conexion SSH y versiones del servidor |
| `remote_list` | Lista archivos/directorios remotos en rutas permitidas |
| `remote_read_text` | Lee archivos de texto remotos con limite de bytes |
| `mysql_query_readonly` | Ejecuta SELECT, SHOW, DESCRIBE, EXPLAIN |
| `mysql_list_tables` | Lista tablas de la base configurada |
| `mysql_describe_table` | Muestra columnas de una tabla |
| `wordpress_users` | Busca usuarios de WordPress en `wp_users` |
| `find_client_columns` | Ubica columnas para clientes, RUC, razon social, contacto |

### Escritura (WebOps Agent — requiere GitHub + SSH key)

| Herramienta | Descripcion |
|---|---|
| `create_branch` | Crea branch en GitHub |
| `commit_changes` | Commit y push automatico |
| `create_pull_request` | Abre PR con descripcion automatica |
| `get_preview_url` | URL de staging para revision |
| `check_deploy_status` | Estado del build y deploy en curso |

---

## Instalacion

```bash
cd mcp_web_connector
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
chmod 600 .env
```

Edita `.env` con la clave privada RSA local (`MCP_WEB_SSH_KEY_FILE`) y la clave de BD (`MCP_WEB_DB_PASSWORD`). No uses `MCP_WEB_SSH_PASSWORD` para este proyecto.

Si la clave RSA esta cifrada, desbloqueala con `ssh-add ~/.ssh/id_rsa` y usa `MCP_WEB_SSH_ALLOW_AGENT=1`, o define `MCP_WEB_SSH_KEY_PASSPHRASE` solo en tu `.env` local.

---

## Configuracion MCP

```json
{
  "mcpServers": {
    "mcperu-web": {
      "command": "/Users/eidergonzaleztamara/Documents/web side/MC_2026/Peru/mcp_web_connector/.venv/bin/python",
      "args": [
        "/Users/eidergonzaleztamara/Documents/web side/MC_2026/Peru/mcp_web_connector/server.py"
      ],
      "env": {
        "MCP_WEB_SSH_HOST": "179.43.82.54",
        "MCP_WEB_SSH_PORT": "22",
        "MCP_WEB_SSH_USER": "mcp-agent",
        "MCP_WEB_SSH_KEY_FILE": "~/.ssh/mc2026/mcp-agent-mcperu-rsa",
        "MCP_WEB_DB_NAME": "bdmcperu",
        "MCP_WEB_DB_USER": "mcp_agent_ro"
      }
    }
  }
}
```

**Nota:** Usar el usuario `mcp-agent` y autenticacion por clave SSH, nunca `root` con password.

---

## Seguridad

Las consultas SQL se bloquean si contienen `UPDATE`, `DELETE`, `DROP`, `ALTER`, `INSERT`, `CREATE`, `TRUNCATE`, `GRANT`, `REVOKE`, `LOAD`, `OUTFILE`, `INFILE`, `CALL`, `SET`, `LOCK` o multiples sentencias.

Las herramientas de archivos solo leen dentro de `MCP_WEB_ALLOWED_ROOTS`.

---

## Usuario mcp-agent en el servidor

El usuario `mcp-agent` es la identidad exclusiva del agente en el servidor `179.43.82.54`. Nunca usa el usuario `root` para operaciones de deploy.

### Especificaciones de seguridad

| Parametro | Valor |
|---|---|
| Usuario del sistema | `mcp-agent` |
| Acceso root | **Nunca** |
| Permisos sudo | Solo `nginx restart` y scripts de deploy |
| Autenticacion | Solo SSH Key RSA 4096 |
| Login por password | **Deshabilitado** |
| Acceso a BD | Solo `SELECT` en `bdmcperu` |
| Historial de comandos | Guardado en `/var/log/mcp-agent/` |

### Estructura de directorios del agente

```
/home/mcp-agent/
├── .ssh/
│   └── authorized_keys          ← Solo la SSH key del agente
├── apps/
│   ├── mcperu/                  ← Produccion (deploy solo via CI/CD)
│   └── mcperu-staging/          ← Staging (preview de cada PR)
└── .bashrc                      ← Shell restringido + logging

/var/log/mcp-agent/
├── access.log                   ← Registro de conexiones SSH
├── deploy.log                   ← Registro de cada deploy
├── staging.log                  ← Registro de actualizaciones de staging
├── rollback.log                 ← Registro de rollbacks
├── sudo.log                     ← Registro de comandos sudo
└── bash_history_YYYYMMDD.log   ← Historial de comandos por dia

/etc/mcp-agent/
└── db.env                       ← Credenciales BD (solo root puede leer)

/etc/sudoers.d/mcp-agent         ← Permisos sudo minimos
/usr/local/bin/deploy-mcperu.sh  ← Script de deploy controlado
/usr/local/bin/update-staging.sh ← Script de actualizacion de staging
/usr/local/bin/rollback-mcperu.sh← Script de rollback
```

### Permisos permitidos al agente

```
✓  git pull / git fetch
✓  git push (branches remotas)
✓  crear branches
✓  ejecutar build (Node/npm si se configura)
✓  sudo /usr/local/bin/deploy-mcperu.sh
✓  sudo /usr/local/bin/update-staging.sh
✓  sudo systemctl restart nginx
✓  sudo systemctl reload nginx
✓  SELECT en base de datos bdmcperu
✓  Lectura de archivos del proyecto web
```

### Permisos prohibidos

```
✗  Acceso como root
✗  sudo en cualquier otro comando
✗  INSERT / UPDATE / DELETE en la base de datos
✗  Lectura de /root, /etc/shadow, credenciales de otros usuarios
✗  rm, chmod, chown directos en produccion
✗  Deploy directo a produccion sin PR aprobado
✗  Acceso FTP
✗  Modificar secretos o .env de produccion
```

### Configuracion SSH aplicada en /etc/ssh/sshd_config

```sshd
Match User mcp-agent
    PasswordAuthentication no
    PubkeyAuthentication yes
    AuthenticationMethods publickey
    AllowTcpForwarding local
    X11Forwarding no
    AllowAgentForwarding no
    PermitTunnel no
    ClientAliveInterval 300
    ClientAliveCountMax 6
    LogLevel VERBOSE
```

---

## Scripts de configuracion

Todos los scripts estan en `mcp_web_connector/scripts/`. Ejecutar en orden como `root` en el servidor:

### Orden de ejecucion

```bash
# En tu Mac (como usuario local):
bash 02-generate-ssh-keys.sh       # Genera el par de claves SSH RSA 4096

# En el servidor (como root):
bash 01-setup-mcp-agent-user.sh    # Crea el usuario y permisos base
PUBLIC_KEY_FILE=/tmp/id_rsa.pub bash 07-install-rsa-public-key.sh
bash 03-setup-db-user.sh           # Crea el usuario MariaDB de solo lectura
bash 04-harden-sshd.sh             # Restringe SSH para mcp-agent
bash 05-setup-staging.sh           # Configura entorno de staging
```

Si quieres que `mcp-agent` acepte exclusivamente la clave RSA nueva, ejecuta el instalador con `REPLACE_AUTHORIZED_KEYS=1` despues de confirmar que tienes una sesion root abierta de respaldo.

### Comandos ejecutados (resumen)

```bash
# 01 — Usuario y permisos
useradd --create-home --shell /bin/bash --groups www-data mcp-agent
passwd -l mcp-agent                              # Bloquear password
mkdir -p /home/mcp-agent/apps/mcperu
mkdir -p /home/mcp-agent/apps/mcperu-staging
mkdir -p /var/log/mcp-agent
chmod 750 /home/mcp-agent

# Sudoers minimos
cat > /etc/sudoers.d/mcp-agent << EOF
mcp-agent ALL=(ALL) NOPASSWD: /bin/systemctl restart nginx
mcp-agent ALL=(ALL) NOPASSWD: /bin/systemctl reload nginx
mcp-agent ALL=(ALL) NOPASSWD: /usr/local/bin/deploy-mcperu.sh
mcp-agent ALL=(ALL) NOPASSWD: /usr/local/bin/update-staging.sh
EOF

# 02 — SSH key RSA (en Mac local)
ssh-keygen -t rsa -b 4096 -o -a 100 -C "mcp-agent-rsa@mcperu.pe" -f ~/.ssh/mc2026/mcp-agent-mcperu-rsa -N ""

# 07 — Instalar clave publica RSA en authorized_keys (en servidor)
PUBLIC_KEY_FILE=/tmp/id_rsa.pub bash 07-install-rsa-public-key.sh

# 03 — Base de datos
mysql -u root -e "CREATE USER 'mcp_agent_ro'@'localhost' IDENTIFIED BY '...';"
mysql -u root -e "GRANT SELECT ON bdmcperu.* TO 'mcp_agent_ro'@'localhost';"
# Credenciales guardadas en /etc/mcp-agent/db.env (solo root)

# 04 — SSH hardening
# Agrega bloque Match User mcp-agent a /etc/ssh/sshd_config
# Backup automatico antes de modificar
systemctl reload sshd

# 05 — Staging
# Nginx en puerto 8080 apuntando a mcperu-staging/
# Preview: http://179.43.82.54:8080
```

---

## WebOps Agent — Flujo de deploy

```
Solicitud de cambio
      │
      ▼
Analizar archivos afectados
      │
      ▼
Crear branch: feature/descripcion
      │
      ▼
Editar archivos (Claude Code + MCP)
      │
      ▼
GitHub Actions: Lint + HTML + JS
      │
      ├── FALLO ──► Reportar error, detener
      │
      ▼ OK
Commit + Push a GitHub
      │
      ▼
Crear Pull Request automatico
      │
      ▼
GitHub Actions: Deploy a Staging
      │
      ▼
Comentar PR con Preview URL
      (http://179.43.82.54:8080)
      │
      ▼
Esperar aprobacion manual del PR
      │
      ▼ Aprobado + Merge a main
GitHub Actions: Deploy a Produccion
      │
      ├── FALLO ──► Rollback automatico al commit anterior
      │
      ▼ OK
Sitio actualizado (https://mcperu.pe)
```

### Secrets requeridos en GitHub

| Secret | Descripcion |
|---|---|
| `MCP_AGENT_SSH_PRIVATE_KEY` | Clave privada RSA del mcp-agent |
| `VERCEL_TOKEN` | Token de Vercel (si se usa Vercel en lugar de SSH) |
| `VERCEL_ORG_ID` | ID de organizacion en Vercel |
| `VERCEL_PROJECT_ID` | ID del proyecto en Vercel |

### Proteccion de la rama main

Configurar en GitHub → Settings → Branches → Add rule → `main`:

- `Require a pull request before merging`
- `Require status checks to pass before merging`
  - Status check requerido: `Lint & Validate`
- `Restrict who can push to matching branches`
- `Do not allow bypassing the above settings`

---

## Estrategia de rollback

### Rollback automatico (GitHub Actions)

Si el deploy a produccion falla (HTTP != 200/301), el workflow revierte automaticamente al commit anterior:

```bash
cd /home/mcp-agent/apps/mcperu
git checkout HEAD~1 -- .
sudo systemctl reload nginx
```

### Rollback manual

```bash
# En el servidor como mcp-agent:
sudo /usr/local/bin/rollback-mcperu.sh produccion 1    # Revertir 1 commit
sudo /usr/local/bin/rollback-mcperu.sh produccion abc1234  # Revertir a commit especifico

# En staging:
sudo /usr/local/bin/rollback-mcperu.sh staging 2       # Revertir 2 commits
```

### Rollback via GitHub

1. Ir al PR que causo el problema.
2. Hacer clic en **Revert** (GitHub crea un PR de reversion automaticamente).
3. Aprobar y mergear el PR de reversion.
4. GitHub Actions hace el deploy del revert automaticamente.

### Log de rollbacks

Cada rollback queda registrado en `/var/log/mcp-agent/rollback.log`:

```
[2026-05-18 14:30:00] ROLLBACK PRODUCCION iniciado por mcp-agent desde 192.168.1.1 22 2341
[2026-05-18 14:30:05] Commit actual: abc1234 — feat: agregar ordenes de servicio en nav
[2026-05-18 14:30:12] ROLLBACK completado. Commit activo: def5678 — version anterior
```

---

## Variables sensibles fuera del repositorio

**Nunca en git:**

| Variable | Ubicacion en servidor | Uso |
|---|---|---|
| SSH private key | `~/.ssh/mc2026/mcp-agent-mcperu-rsa` (Mac local) | Conexion del agente |
| DB password (mcp_agent_ro) | `/etc/mcp-agent/db.env` | Lectura de BD |
| DB password (root) | Variable de entorno en servidor | Administracion |
| VERCEL_TOKEN | GitHub Secrets | Deploy a Vercel |
| MCP_AGENT_SSH_PRIVATE_KEY | GitHub Secrets | CI/CD SSH access |

El archivo `.env` del conector esta en `.gitignore` y nunca se sube al repositorio.

---

## Conexion con Ordenes de Servicio

El sistema `Peru/ordenes/` tiene una tabla real en MariaDB (`orden_servicio`). Sus cambios siguen el flujo WebOps:

- Cambios en `ordenes-servicio.js` → branch + PR + staging preview + aprobacion + merge
- Consultas a BD → siempre via `mysql_query_readonly` del MCP
- Estado funcional vigente del modulo → ver `Peru/ordenes/README.md`

### Estado de la tabla `orden_servicio` (Fase 2 — 2026-05-30)

| Campo | Detalle |
|---|---|
| Tabla | `orden_servicio` |
| Columnas | 25 — ver `database/ordenes_servicio_schema.sql` y `database/migrations/` |
| Campo consecutivo | `numero_os` VARCHAR(10) con `UNIQUE KEY uq_numero_os` |
| Maximo consecutivo | `000703` (4 registros activos) |
| AUTO_INCREMENT id | 5 (proximo id seria 5) |
| Estados presentes | `Creada` (3), `Facturacion validada` (1) |
| Soft-delete | Implementado con `deleted_at`, `deleted_by` y estado `ELIMINADA` |
| Tabla de secuencia | `secuencias`, fila `orden_servicio`, valor actual `703` |

> El respaldo completo de Fase 1 (schema, datos, checksums) esta en `~/mcperu_mariadb_export_20260529_130922/` en la maquina local.

### Riesgo resuelto en Fase 2

El `numero_os` ya no se genera en `localStorage`. La creacion de OS debe pasar por `api/create-order.php`, que toma el siguiente valor desde `secuencias` en MariaDB. El navegador conserva `localStorage` solo como cache.
