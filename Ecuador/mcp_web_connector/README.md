# MCP Web Connector — Media Commerce Ecuador

Conector MCP para acceso SSH de lectura y escritura al servidor de Ecuador (`mediacommerce.ec`).

---

## Servidor

| Parámetro | Valor |
|---|---|
| Host | `51.79.104.194` |
| Puerto SSH | `22` |
| Dominio | `https://www.mediacommerce.ec` |
| Web root cPanel | `/home/<usuario>/public_html/` |

---

## Instalación rápida

```bash
cd "Ecuador/mcp_web_connector"

# 1. Crear entorno virtual
python3 -m venv .venv

# 2. Instalar dependencias
.venv/bin/pip install -r requirements.txt

# 3. Configurar credenciales
cp .env.example .env
# Editar .env con usuario SSH y contraseña o llave privada

# 4. Registrar en Claude Code
# Settings → MCP Servers → Add from file → mcp-config.example.json
```

---

## Configurar el .env

Edita `Ecuador/mcp_web_connector/.env`:

```env
MCP_WEB_SSH_HOST=51.79.104.194
MCP_WEB_SSH_PORT=22
MCP_WEB_SSH_USER=root           # o el usuario cPanel
MCP_WEB_SSH_PASSWORD=tu_clave   # o usar MCP_WEB_SSH_KEY_FILE
MCP_WEB_ALLOWED_ROOTS=/home,/var/www,/usr/local/apache/htdocs
```

---

## Skills disponibles

### Diagnóstico
| Skill | Descripción |
|---|---|
| `config_summary` | Verifica que el .env cargó correctamente |
| `ssh_health` | Prueba SSH y retorna info del servidor (hostname, PHP, disco) |
| `get_server_host_key` | Obtiene la host key del servidor para verificación estricta |

### Lectura remota
| Skill | Descripción |
|---|---|
| `remote_list` | Lista archivos de un directorio remoto |
| `remote_read_text` | Lee un archivo de texto remoto |

### Escritura y deploy ✅
| Skill | Descripción |
|---|---|
| `remote_write_text` | Escribe/reemplaza un archivo de texto en el servidor (con backup automático en /tmp) |
| `remote_write_binary` | Sube un archivo binario local (imagen, font, etc.) al servidor |
| `remote_deploy_files` | Despliega múltiples archivos en una sola llamada |
| `remote_exec` | Ejecuta comandos permitidos en el servidor (ls, cp, chmod, service apache2 reload…) |

---

## Ejemplo de deploy

### Subir una página nueva

```json
{
  "name": "remote_write_text",
  "arguments": {
    "path": "/home/<usuario>/public_html/internet-corporativo-ecuador.html",
    "content": "<contenido del archivo>"
  }
}
```

### Deploy masivo de archivos

```json
{
  "name": "remote_deploy_files",
  "arguments": {
    "files_json": "[{\"local\": \"/ruta/local/archivo.html\", \"remote\": \"/home/usuario/public_html/archivo.html\"}]"
  }
}
```

### Verificar deploy

```json
{
  "name": "remote_list",
  "arguments": {
    "path": "/home/<usuario>/public_html",
    "max_entries": 50
  }
}
```

---

## Flujo de deploy recomendado

1. `config_summary` → verificar que el .env cargó
2. `ssh_health` → confirmar que el servidor está activo
3. `remote_list` → ver estructura actual de `/home/<usuario>/public_html`
4. `remote_deploy_files` → subir los archivos cambiados
5. `remote_list` → verificar que los archivos están en el servidor

---

## Diferencias con el conector Peru

| | Peru (`mcperu-web`) | Ecuador (`mcecuador-web`) |
|---|---|---|
| Host | `179.43.82.54` | `51.79.104.194` |
| Dominio | `mcperu.pe` | `mediacommerce.ec` |
| Web root | `/var/www/html/` | `/home/<usuario>/public_html/` |
| Base de datos | MariaDB `bdmcperu` | No configurada |
| Skills DB | Sí (mysql_*) | No (desactivadas por default) |

*Última actualización: 2026-05-28 — v0.1.0*
