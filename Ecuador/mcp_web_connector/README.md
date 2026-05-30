# MCP Web Connector — Media Commerce Ecuador

> **Todo agente IA que necesite leer, modificar o desplegar archivos en `www.mediacommerce.ec` DEBE hacerlo exclusivamente a través de este MCP. No se permite acceso directo vía SSH, FTP, cPanel ni ningún otro método.**

---

## Conexión rápida (datos confirmados en producción)

| Parámetro | Valor |
|---|---|
| **Hostname** | `hc-02.webserver.ec` |
| **IP** | `51.79.106.41` |
| **Puerto SSH** | `22` |
| **Usuario** | `mediaco2` |
| **Llave privada** | `~/.ssh/mc2026/mcecuador-mediaco2-rsa` |
| **Web root** | `/home/mediaco2/public_html/` |
| **Tipo hosting** | cPanel (Apache) |
| **cPanel** | `https://hc-02.webserver.ec:2083/` |
| **Conexión** | ✅ Verificada 2026-05-28 |

---

## Instalación (solo la primera vez)

```bash
cd "Ecuador/mcp_web_connector"

# 1. Crear entorno virtual
python3 -m venv .venv

# 2. Instalar dependencias
.venv/bin/pip install -r requirements.txt

# 3. El .env ya está configurado con las credenciales reales
# Si necesitas regenerarlo: cp .env.example .env

# 4. Registrar en Claude Code
# Settings → MCP Servers → agregar el bloque de mcp-config.example.json
```

### Registrar en Claude Code (`~/.claude/settings.json`)

```json
{
  "mcpServers": {
    "mcecuador-web": {
      "command": "/Users/eidergonzaleztamara/Documents/web side/MC_2026/Ecuador/mcp_web_connector/.venv/bin/python",
      "args": [
        "/Users/eidergonzaleztamara/Documents/web side/MC_2026/Ecuador/mcp_web_connector/server.py"
      ],
      "env": {
        "MCP_WEB_SSH_HOST": "hc-02.webserver.ec",
        "MCP_WEB_SSH_PORT": "22",
        "MCP_WEB_SSH_USER": "mediaco2",
        "MCP_WEB_SSH_KEY_FILE": "/Users/eidergonzaleztamara/.ssh/mc2026/mcecuador-mediaco2-rsa",
        "MCP_WEB_ALLOWED_ROOTS": "/home/mediaco2/public_html,/home/mediaco2,/home"
      }
    }
  }
}
```

---

## Skills disponibles

### Diagnóstico — ejecutar primero

| Skill | Descripción | Cuándo usar |
|---|---|---|
| `config_summary` | Verifica que el .env cargó | **Siempre primero** — si falla, no continuar |
| `ssh_health` | Prueba SSH, retorna hostname/PHP/disco | Antes de cualquier deploy |
| `get_server_host_key` | Obtiene fingerprint del servidor | Una vez, para completar `MCP_WEB_SSH_KNOWN_HOST_KEY` |

### Lectura remota

| Skill | Parámetros | Uso típico |
|---|---|---|
| `remote_list` | `path`, `max_entries` | Ver contenido del servidor, verificar deploy |
| `remote_read_text` | `path`, `max_bytes` | Comparar archivo local vs. producción |

### Escritura y deploy

| Skill | Parámetros | Uso típico |
|---|---|---|
| `remote_write_text` | `path`, `content` | Subir/reemplazar un archivo HTML, CSS o JS |
| `remote_write_binary` | `path`, `local_path` | Subir imágenes, fuentes, binarios |
| `remote_deploy_files` | `files_json` | **Deploy masivo — varios archivos a la vez** |
| `remote_exec` | `command` | Comandos post-deploy (ls, cp, chmod, service reload) |

---

## Flujo de deploy estándar

### Paso 1 — Verificar conexión

```json
{ "name": "config_summary" }
```
Resultado esperado: `ssh_host: "hc-02.webserver.ec"`, `has_ssh_key_file: true`

### Paso 2 — Confirmar servidor activo

```json
{ "name": "ssh_health" }
```
Resultado esperado: `user: "mediaco2"`, `host: "hc-02.webserver.ec"`

### Paso 3 — Ver estado actual del servidor

```json
{
  "name": "remote_list",
  "arguments": {
    "path": "/home/mediaco2/public_html",
    "max_entries": 100
  }
}
```

### Paso 4 — Subir archivos

**Un solo archivo:**
```json
{
  "name": "remote_write_text",
  "arguments": {
    "path": "/home/mediaco2/public_html/index.html",
    "content": "<!-- contenido completo del archivo -->"
  }
}
```

**Múltiples archivos (recomendado para deploy):**
```json
{
  "name": "remote_deploy_files",
  "arguments": {
    "files_json": "[
      {\"local\": \"/Users/eidergonzaleztamara/Documents/web side/MC_2026/Ecuador/internet-corporativo-ecuador.html\",
       \"remote\": \"/home/mediaco2/public_html/internet-corporativo-ecuador.html\"},
      {\"local\": \"/Users/eidergonzaleztamara/Documents/web side/MC_2026/Ecuador/index.html\",
       \"remote\": \"/home/mediaco2/public_html/index.html\"}
    ]"
  }
}
```

> Cada archivo tiene **backup automático** en `/tmp/mcp_backup/` antes de sobreescribirse.

### Paso 5 — Verificar deploy

```json
{
  "name": "remote_list",
  "arguments": {
    "path": "/home/mediaco2/public_html",
    "max_entries": 100
  }
}
```

---

## Rutas de referencia en el servidor

| Elemento | Ruta en servidor |
|---|---|
| Web root | `/home/mediaco2/public_html/` |
| Páginas raíz | `/home/mediaco2/public_html/*.html` |
| Soluciones | `/home/mediaco2/public_html/soluciones/` |
| Asesoramiento | `/home/mediaco2/public_html/asesoramiento/` |
| Normatividad | `/home/mediaco2/public_html/normatividad-y-regulaciones/` |
| Backups MCP | `/tmp/mcp_backup/` |

## Rutas de referencia en el equipo local

| Elemento | Ruta local |
|---|---|
| Proyecto Ecuador | `/Users/eidergonzaleztamara/Documents/web side/MC_2026/Ecuador/` |
| Llave SSH privada | `/Users/eidergonzaleztamara/.ssh/mc2026/mcecuador-mediaco2-rsa` |
| Llave SSH pública | `/Users/eidergonzaleztamara/.ssh/mc2026/mcecuador-mediaco2-rsa.pub` |
| MCP connector | `/Users/eidergonzaleztamara/Documents/web side/MC_2026/Ecuador/mcp_web_connector/` |

---

## Comandos post-deploy útiles

### Verificar permisos de un archivo
```json
{
  "name": "remote_exec",
  "arguments": { "command": "ls -la /home/mediaco2/public_html/internet-corporativo-ecuador.html" }
}
```

### Corregir permisos si es necesario
```json
{
  "name": "remote_exec",
  "arguments": { "command": "chmod 644 /home/mediaco2/public_html/internet-corporativo-ecuador.html" }
}
```

### Ver espacio en disco
```json
{
  "name": "remote_exec",
  "arguments": { "command": "df -h /" }
}
```

---

## Estado del deploy en producción (2026-05-28)

| Archivo | Servidor | HTTP |
|---|---|---|
| `index.html` + 23 páginas raíz | ✅ | 200 |
| `asesoramiento/*.html` (4) | ✅ | 200 |
| `soluciones/*.html` (4) | ✅ | 200 |
| `normatividad-y-regulaciones/*.html` (2) | ✅ | 200 |
| `internet-corporativo-ecuador.html` | ✅ | 200 |
| `internet-dedicado-ecuador.html` | ✅ | 200 |
| `canales-de-datos-ecuador.html` | ✅ | 200 |
| `fibra-optica-empresas-ecuador.html` | ✅ | 200 |

**Total: 31 páginas HTML en producción.**

---

## Diferencias con el MCP de Perú

| | Perú (`mcperu-web`) | Ecuador (`mcecuador-web`) |
|---|---|---|
| Host | `179.43.82.54` | `hc-02.webserver.ec` |
| Usuario | `mcp-agent` / `root` | `mediaco2` |
| Llave | `mcp-agent-mcperu` | `mcecuador-mediaco2-rsa` |
| Web root | `/var/www/html/` | `/home/mediaco2/public_html/` |
| Tipo | VPS / Apache | cPanel / Apache |
| BD | MariaDB `bdmcperu` | No configurada |

---

## Seguridad

- La llave privada `mcecuador-mediaco2-rsa` está en `~/.ssh/mc2026/` con permisos `600`.
- La llave pública fue autorizada en cPanel SSH Access para el usuario `mediaco2`.
- El `.env` tiene credenciales reales — nunca subirlo a git (está en `.gitignore`).
- El MCP hace backup automático antes de sobreescribir cualquier archivo.
- Comandos `remote_exec`: solo whitelist permitida (ls, find, cp, chmod, service reload…).

*Última actualización: 2026-05-28 — v0.1.0 — Conexión verificada, 31 páginas en producción*
