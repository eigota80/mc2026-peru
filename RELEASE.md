# Release v2026.05.18 — Media Commerce Peru

## Estado: DESPLEGADO EN PRODUCCION ✅

**Fecha:** 2026-05-18
**URL:** https://www.mcperu.pe
**Servidor:** 179.43.82.54 — Apache — `/var/www/html/`
**Tag git:** `v2026.05.18`
**Branch:** `main`

---

## Commits incluidos

| Hash | Descripcion |
|---|---|
| `405efe5` | feat: base del sitio web Peru con navegacion completa |
| `288433c` | feat: sistema de Ordenes de Servicio — modulo comercial completo |
| `7dc520d` | feat: WebOps Agent — GitHub Actions CI/CD + MCP web connector + scripts |
| `5a4bc18` | chore: release v2026.05.18 — estado aprobado |

---

## Cambios entregados

### Sitio web Peru — navegacion

- [x] Enlace "Ordenes de servicio" en seccion EMPRESA del menu — 33 paginas actualizadas
- [x] `sitemap.xml` actualizado con entrada para Ordenes de servicio
- [x] `robots.txt` creado con reglas de indexacion correctas

### Modulo Ordenes de Servicio

- [x] Login separado en `ordenes-servicio.html` + `login.js`
- [x] App completa en `index.html` + `ordenes-servicio.js`
- [x] PDF generado nativamente (sin librerias externas)
- [x] Logo embebido como base64 — funciona en `file://` y produccion
- [x] Firmas PDF corregidas: Representante Legal en `x=188`
- [x] Campos corporativos eliminados del PDF (solo logo en header)
- [x] Orden PDF: tabla servicios → observaciones → facilidades → firmas
- [x] Control de acceso por rol (3 capas de proteccion)
- [x] Reset automatico de ordenes por `DATA_VERSION`
- [x] Boton "Reiniciar ordenes" en panel Administrador

### Infraestructura WebOps

- [x] GitHub Actions workflow (`.github/workflows/webops-deploy.yml`)
- [x] SSH key Ed25519 generada para `mcp-agent` (`~/.ssh/mc2026/mcp-agent-mcperu`)
- [x] `~/.ssh/config` con entrada `mcperu-agent`
- [x] Scripts de configuracion del servidor (6 scripts en `mcp_web_connector/scripts/`)
- [x] MCP web connector documentado

---

## Archivos desplegados en produccion

| Archivo en servidor | Tamaño | Fecha deploy |
|---|---|---|
| `/var/www/html/*.html` (17 paginas raiz) | varios | 2026-05-18 |
| `/var/www/html/asesoramiento/*.html` (4) | varios | 2026-05-18 |
| `/var/www/html/blog/*.html` (6) | varios | 2026-05-18 |
| `/var/www/html/soluciones/*.html` (4) | varios | 2026-05-18 |
| `/var/www/html/normatividad-y-regulaciones/*.html` (2) | varios | 2026-05-18 |
| `/var/www/html/Ordenes de servicios/ordenes-servicio.html` | 1,630 bytes | 2026-05-18 |
| `/var/www/html/Ordenes de servicios/index.html` | 14,162 bytes | 2026-05-18 |
| `/var/www/html/Ordenes de servicios/login.js` | 6,358 bytes | 2026-05-18 |
| `/var/www/html/Ordenes de servicios/ordenes-servicio.js` | 148,518 bytes | 2026-05-18 |
| `/var/www/html/Ordenes de servicios/ordenes-servicio.css` | 10,833 bytes | 2026-05-18 |
| `/var/www/html/Ordenes de servicios/Logo MC (...).png` | 76,263 bytes | 2026-05-18 |
| `/var/www/html/sitemap.xml` | 5,593 bytes | 2026-05-18 |
| `/var/www/html/robots.txt` | 330 bytes | 2026-05-18 |

---

## Verificacion HTTP post-deploy

| URL | HTTP | Resultado |
|---|---|---|
| `https://www.mcperu.pe/` | 200 | OK |
| `/Ordenes%20de%20servicios/ordenes-servicio.html` | 200 | OK |
| `/Ordenes%20de%20servicios/index.html` | 200 | OK |
| `/robots.txt` | 200 | OK |
| `/sitemap.xml` | 200 | OK |

---

## Notas tecnicas del deploy

### Problema con rsync y espacios en nombres de directorio

`rsync` con `sshpass` no transfiere correctamente directorios con espacios. El directorio `Ordenes de servicios/` llega al servidor como `Ordenes/`. Workaround aplicado en cada deploy:

```bash
sshpass -p "$PASS" ssh root@179.43.82.54 \
  "cp -r /var/www/html/Ordenes/. '/var/www/html/Ordenes de servicios/' && rm -rf /var/www/html/Ordenes"
```

### Versionado de cache del navegador

El `<script src>` en `index.html` usa query string para invalidar cache:

```html
<script src="ordenes-servicio.js?v=20260518-reset-v1"></script>
```

Incrementar el sufijo `-vN` en cada deploy que cambie el JS.

---

## Pendiente para activar CI/CD completo

```bash
# 1. Conectar repositorio a GitHub
git remote add origin https://github.com/TU_ORG/MC_2026.git
git push -u origin main --tags

# 2. En el servidor como root — ejecutar en orden:
bash Peru/mcp_web_connector/scripts/01-setup-mcp-agent-user.sh
bash Peru/mcp_web_connector/scripts/03-setup-db-user.sh
bash Peru/mcp_web_connector/scripts/04-harden-sshd.sh
bash Peru/mcp_web_connector/scripts/05-setup-staging.sh

# 3. Instalar clave publica del agente en el servidor:
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFlTW1ICfZTOCime/9WkdVyFTTcj+UVywj2hYGrObmsr mcp-agent@mcperu.pe-20260518" \
  >> /home/mcp-agent/.ssh/authorized_keys

# 4. Agregar secrets en GitHub:
#    MCP_AGENT_SSH_PRIVATE_KEY = contenido de ~/.ssh/mc2026/mcp-agent-mcperu

# 5. Proteger rama main:
#    GitHub → Settings → Branches → Add rule → main
#    Activar: Require PR + Require status checks (Lint & Validate)
```

---

## Rollback disponible

```bash
# Manual en el servidor:
sshpass -p "$PASS" ssh root@179.43.82.54 \
  "cd '/var/www/html/Ordenes de servicios' && git checkout HEAD~1 -- . && systemctl reload httpd"

# Via git (cuando GitHub este configurado):
# 1. Ir al commit del problema en GitHub
# 2. Crear PR de reversion
# 3. Mergear → GitHub Actions hace el deploy automaticamente
```
