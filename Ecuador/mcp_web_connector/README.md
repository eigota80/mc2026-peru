# MCP Web Connector — Media Commerce Ecuador

> **Todo agente IA que necesite leer, modificar o desplegar archivos en `www.mediacommerce.ec` DEBE hacerlo exclusivamente a través de este MCP. No se permite acceso directo vía SSH, FTP, cPanel File Manager ni ningún otro método.**

---

## Datos del servidor

| Parámetro | Valor |
|---|---|
| **IP** | `51.79.104.194` |
| **Puerto SSH** | `22` |
| **Tipo de hosting** | cPanel (Apache) |
| **Panel cPanel** | `https://51.79.104.194:2083/` |
| **Dominio** | `https://www.mediacommerce.ec` |
| **Web root** | `/home/<usuario_cpanel>/public_html/` |

> El usuario cPanel exacto se descubre ejecutando `remote_list /home` una vez conectado.

---

## Instalación (solo la primera vez)

```bash
cd "Ecuador/mcp_web_connector"

# 1. Crear entorno virtual Python
python3 -m venv .venv

# 2. Instalar dependencias
.venv/bin/pip install -r requirements.txt

# 3. Configurar credenciales
cp .env.example .env
# Editar .env con las credenciales SSH reales (ver sección Credenciales)

# 4. Registrar en Claude Code
# Settings → MCP Servers → copiar bloque de mcp-config.example.json
# — O bien agregar en ~/.claude/settings.json la sección mcpServers
```

---

## Credenciales — cómo completar el .env

Edita `Ecuador/mcp_web_connector/.env`:

```env
MCP_WEB_SSH_HOST=51.79.104.194
MCP_WEB_SSH_PORT=22

# Opción A: usuario root con contraseña
MCP_WEB_SSH_USER=root
MCP_WEB_SSH_PASSWORD=tu_contraseña_aqui

# Opción B: usuario cPanel con contraseña
MCP_WEB_SSH_USER=nombre_usuario_cpanel
MCP_WEB_SSH_PASSWORD=tu_contraseña_cpanel

# Opción C: llave privada (descomentar)
# MCP_WEB_SSH_USER=root
# MCP_WEB_SSH_KEY_FILE=/ruta/absoluta/a/llave_privada

# Host key para verificación estricta (obtener con get_server_host_key)
# MCP_WEB_SSH_KNOWN_HOST_KEY=ssh-ed25519 AAAA...

# Rutas permitidas en el servidor
MCP_WEB_ALLOWED_ROOTS=/home,/var/www,/usr/local/apache/htdocs
```

> El servidor Ecuador ya aparece en `~/.ssh/known_hosts` como `mediacommerce.ec` — confirma que SSH fue usado antes.

---

## Skills disponibles

### Diagnóstico

| Skill | Cuándo usarla |
|---|---|
| `config_summary` | **Siempre primero** — verifica que el .env cargó. Si falla, no continuar. |
| `ssh_health` | Antes de cualquier deploy — confirma que el servidor está activo. Retorna hostname, PHP, disco. |
| `get_server_host_key` | Una sola vez — para obtener el fingerprint y ponerlo en `MCP_WEB_SSH_KNOWN_HOST_KEY`. |

### Lectura remota

| Skill | Parámetros clave | Uso típico |
|---|---|---|
| `remote_list` | `path`, `max_entries` | Explorar web root, verificar que archivos llegaron |
| `remote_read_text` | `path`, `max_bytes` | Leer un archivo de producción para comparar con local |

### Escritura y deploy ✅

| Skill | Parámetros clave | Uso típico |
|---|---|---|
| `remote_write_text` | `path`, `content` | Escribir/reemplazar un archivo HTML, CSS o JS (backup automático en `/tmp/mcp_backup/`) |
| `remote_write_binary` | `path`, `local_path` | Subir imagen o fuente desde el equipo local |
| `remote_deploy_files` | `files_json`, `base_local`, `base_remote` | **Deploy masivo** — varios archivos en una sola llamada |
| `remote_exec` | `command` | Comandos seguros post-deploy (ls, cp, chmod, service apache2 reload…) |

---

## Flujo de deploy estándar

### Paso 1 — Verificar conexión

```json
{ "name": "config_summary" }
```
Debe retornar `ssh_host: "51.79.104.194"`. Si falla: revisar `.env`.

### Paso 2 — Confirmar servidor activo

```json
{ "name": "ssh_health" }
```
Retorna hostname, whoami, disco disponible. Si falla: el servidor está caído.

### Paso 3 — Descubrir web root

```json
{ "name": "remote_list", "arguments": { "path": "/home", "max_entries": 20 } }
```
Muestra los usuarios cPanel. El web root es `/home/<usuario>/public_html/`.

### Paso 4 — Ver estado actual del servidor

```json
{
  "name": "remote_list",
  "arguments": {
    "path": "/home/<usuario>/public_html",
    "max_entries": 100
  }
}
```

### Paso 5 — Subir archivos

```json
{
  "name": "remote_deploy_files",
  "arguments": {
    "files_json": "[
      {\"local\": \"/Users/eidergonzaleztamara/Documents/web side/MC_2026/Ecuador/internet-corporativo-ecuador.html\",
       \"remote\": \"/home/<usuario>/public_html/internet-corporativo-ecuador.html\"},
      {\"local\": \"/Users/eidergonzaleztamara/Documents/web side/MC_2026/Ecuador/index.html\",
       \"remote\": \"/home/<usuario>/public_html/index.html\"}
    ]"
  }
}
```

Cada archivo tiene backup automático en `/tmp/mcp_backup/` antes de sobreescribirse.

### Paso 6 — Verificar deploy

```json
{
  "name": "remote_list",
  "arguments": { "path": "/home/<usuario>/public_html", "max_entries": 50 }
}
```

---

## Archivos pendientes de deploy (2026-05-28)

Estos archivos fueron creados/modificados localmente y aún no están en el servidor:

### Páginas SEO nuevas (crear en servidor)
```
Ecuador/internet-corporativo-ecuador.html  → public_html/internet-corporativo-ecuador.html
Ecuador/internet-dedicado-ecuador.html     → public_html/internet-dedicado-ecuador.html
Ecuador/canales-de-datos-ecuador.html      → public_html/canales-de-datos-ecuador.html
Ecuador/fibra-optica-empresas-ecuador.html → public_html/fibra-optica-empresas-ecuador.html
```

### Páginas con nav actualizado (reemplazar en servidor)
```
Ecuador/index.html               → public_html/index.html
Ecuador/asesoramiento.html       → public_html/asesoramiento.html
Ecuador/cobertura.html           → public_html/cobertura.html
Ecuador/contactanos.html         → public_html/contactanos.html
Ecuador/encuesta-de-satisfaccion.html → public_html/encuesta-de-satisfaccion.html
Ecuador/gracias.html             → public_html/gracias.html
Ecuador/informacion-tecnica.html → public_html/informacion-tecnica.html
Ecuador/normas-y-regulaciones.html → public_html/normas-y-regulaciones.html
Ecuador/pqrs.html                → public_html/pqrs.html
Ecuador/preguntas-frecuentes.html → public_html/preguntas-frecuentes.html
Ecuador/quienes-somos.html       → public_html/quienes-somos.html
Ecuador/seguridad.html           → public_html/seguridad.html
Ecuador/soluciones.html          → public_html/soluciones.html
Ecuador/sumate-al-equipo.html    → public_html/sumate-al-equipo.html
Ecuador/tips-de-seguridad.html   → public_html/tips-de-seguridad.html
Ecuador/velocimetro.html         → public_html/velocimetro.html
Ecuador/asesoramiento/informacion-tecnica.html   → public_html/asesoramiento/informacion-tecnica.html
Ecuador/asesoramiento/preguntas-frecuentes.html  → public_html/asesoramiento/preguntas-frecuentes.html
Ecuador/asesoramiento/seguridad.html             → public_html/asesoramiento/seguridad.html
Ecuador/asesoramiento/tips-de-seguridad.html     → public_html/asesoramiento/tips-de-seguridad.html
Ecuador/soluciones/cloud.html        → public_html/soluciones/cloud.html
Ecuador/soluciones/collaboration.html → public_html/soluciones/collaboration.html
Ecuador/soluciones/connection.html   → public_html/soluciones/connection.html
Ecuador/soluciones/security.html     → public_html/soluciones/security.html
Ecuador/normatividad-y-regulaciones/derechos-de-los-abonados.html → public_html/normatividad-y-regulaciones/derechos-de-los-abonados.html
Ecuador/normatividad-y-regulaciones/reglamentos-del-consumidor.html → public_html/normatividad-y-regulaciones/reglamentos-del-consumidor.html
```

---

## Comandos post-deploy útiles

### Recargar Apache (si se modifican configs)
```json
{
  "name": "remote_exec",
  "arguments": { "command": "service apache2 reload" }
}
```

### Verificar permisos de un archivo
```json
{
  "name": "remote_exec",
  "arguments": { "command": "ls -la /home/<usuario>/public_html/internet-corporativo-ecuador.html" }
}
```

### Corregir permisos si es necesario
```json
{
  "name": "remote_exec",
  "arguments": { "command": "chmod 644 /home/<usuario>/public_html/internet-corporativo-ecuador.html" }
}
```

---

## Diferencias con el MCP de Perú

| | Perú (`mcperu-web`) | Ecuador (`mcecuador-web`) |
|---|---|---|
| Host | `179.43.82.54` | `51.79.104.194` |
| Tipo servidor | VPS / Apache | cPanel / Apache |
| Web root | `/var/www/html/` | `/home/<usuario>/public_html/` |
| Base de datos | MariaDB `bdmcperu` | No configurada |
| Skills DB | Sí (mysql_*) | Desactivadas por defecto |
| Versión | `0.3.0` | `0.1.0` |

---

## Seguridad

- Nunca leer ni modificar `.env`, backups, credenciales ni archivos fuera de las raíces permitidas.
- El MCP hace backup automático de cada archivo antes de sobreescribirlo (`/tmp/mcp_backup/`).
- Comandos remotos: solo los de la whitelist (`ls`, `find`, `cp`, `chmod`, `service apache2 reload`…).
- Variables sensibles **nunca en git**: `.env` está en `.gitignore`.

*Última actualización: 2026-05-28 — v0.1.0*
