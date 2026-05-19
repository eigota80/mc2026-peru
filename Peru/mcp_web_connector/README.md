# MCP Web Connector — Media Commerce Peru

Servidor MCP local por `stdio` para conectarse al hosting web y a la base MariaDB `bdmcperu` por SSH.

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

Edita `.env` con las claves reales.

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
        "MCP_WEB_SSH_KEY_PATH": "~/.ssh/mc2026/mcp-agent-mcperu",
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
| Autenticacion | Solo SSH Key (Ed25519) |
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
    AllowTcpForwarding no
    X11Forwarding no
    AllowAgentForwarding no
    PermitTunnel no
    ChrootDirectory /home/mcp-agent
    ClientAliveInterval 300
    ClientAliveCountMax 6
    LogLevel VERBOSE
```

---

## Scripts de configuracion

Todos los scripts estan en `mcp_web_connector/scripts/`. Ejecutar en orden como `root` en el servidor:

### Orden de ejecucion

```bash
# En el servidor (como root):
bash 01-setup-mcp-agent-user.sh    # Crea el usuario y permisos base
bash 03-setup-db-user.sh           # Crea el usuario MariaDB de solo lectura
bash 04-harden-sshd.sh             # Restringe SSH para mcp-agent
bash 05-setup-staging.sh           # Configura entorno de staging

# En tu Mac (como usuario local):
bash 02-generate-ssh-keys.sh       # Genera el par de claves SSH Ed25519
```

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

# 02 — SSH key (en Mac local)
ssh-keygen -t ed25519 -C "mcp-agent@mcperu.pe" -f ~/.ssh/mc2026/mcp-agent-mcperu -N ""

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
| `MCP_AGENT_SSH_PRIVATE_KEY` | Clave privada Ed25519 del mcp-agent |
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
| SSH private key | `~/.ssh/mc2026/mcp-agent-mcperu` (Mac local) | Conexion del agente |
| DB password (mcp_agent_ro) | `/etc/mcp-agent/db.env` | Lectura de BD |
| DB password (root) | Variable de entorno en servidor | Administracion |
| VERCEL_TOKEN | GitHub Secrets | Deploy a Vercel |
| MCP_AGENT_SSH_PRIVATE_KEY | GitHub Secrets | CI/CD SSH access |

El archivo `.env` del conector esta en `.gitignore` y nunca se sube al repositorio.

---

## Conexion con Ordenes de Servicio

El sistema `Peru/Ordenes de servicios/` opera en `localStorage` y no requiere backend. Sus cambios siguen el mismo flujo WebOps:

- Cambios en `ordenes-servicio.js` → branch + PR + staging preview + aprobacion + merge
- Actualizacion del logo (`LOGO_B64`) → mismo flujo
- Integracion futura con MariaDB → jobs adicionales en el workflow de Actions

Para la integracion futura con MariaDB, el usuario `mcp_agent_ro` (solo SELECT) es la identidad de acceso recomendada desde el conector MCP.
