# CLAUDE.md — Proyecto MC Ecuador 2026

> **Regla de oro: toda IA que trabaje en este proyecto DEBE usar el MCP `mcecuador-web` para cualquier acceso, modificación o deploy al servidor de producción. El acceso directo vía SSH, FTP, cPanel File Manager o cualquier otro método NO está permitido.**

---

## Índice

1. [Identidad del proyecto](#identidad)
2. [Regla de uso exclusivo del MCP](#mcp-obligatorio)
3. [Estructura del proyecto](#estructura)
4. [Servidor de producción](#servidor)
5. [Páginas SEO creadas](#paginas-seo)
6. [Identidad Ecuador vs. Perú](#diferencias)
7. [Flujo de trabajo y deploy](#flujo-de-trabajo)
8. [Tareas pendientes](#pendientes)

---

## Identidad

| Parámetro | Valor |
|---|---|
| **Dominio canónico** | `https://www.mediacommerce.ec` |
| **Mercado** | Ecuador — B2B — Telecomunicaciones, conectividad, cloud, seguridad |
| **Idioma** | Español, variante Ecuador (`es-EC`) |
| **Moneda JSON-LD** | USD |
| **Regulador telecom** | ARCOTEL (`http://www.arcotel.gob.ec/`) |
| **GTM** | `GTM-N4SCNV2` (compartido con Perú) |
| **GA4** | No configurado (solo GTM) |

### Contacto

| Canal | Dato |
|---|---|
| Email principal | `servicioalcliente@mediacommerce.ec` |
| Teléfono fijo | `+593 (2) 394 2280 A 2289` |
| Línea gratuita | `01 800 633 423` |
| Celular 1 | `+593 98 759 2186` |
| Celular 2 | `+593 98 786 1855` |
| WhatsApp | `https://wa.me/593987592186` |
| Webmail | `https://webmail.mediacommerce.ec` |

### Redes sociales

| Red | URL |
|---|---|
| Facebook | `https://www.facebook.com/MediaCommerceOficial` |
| Twitter | `https://twitter.com/media_commerce` |
| LinkedIn | `https://www.linkedin.com/company/media-commerce-partners-s.a/` |
| YouTube | `https://www.youtube.com/channel/UCsE50rQtm2X_JjYHuEFWpmA` |
| Instagram | **No existe para Ecuador — NO agregar** |

---

## MCP Obligatorio

**Ninguna IA puede acceder ni modificar el servidor de Ecuador sin pasar por el MCP `mcecuador-web`.**

### Servidor de producción

| Parámetro | Valor |
|---|---|
| **IP** | `51.79.104.194` |
| **Puerto SSH** | `22` |
| **Protocolo** | SSH + SFTP (cPanel hosting, Apache) |
| **cPanel** | `https://51.79.104.194:2083/` |
| **Web root** | `/home/<usuario_cpanel>/public_html/` |
| **SSH previo confirmado** | `mediacommerce.ec` en `~/.ssh/known_hosts` |

### Configuración del MCP

| Parámetro | Valor |
|---|---|
| Servidor | `Ecuador/mcp_web_connector/server.py` |
| Protocolo | stdio JSON-RPC 2.0 (MCP 2024-11-05) |
| ID en Claude Code | `mcecuador-web` |
| Config de ejemplo | `Ecuador/mcp_web_connector/mcp-config.example.json` |
| Credenciales | `Ecuador/mcp_web_connector/.env` |

### Pasos para activar el MCP (primera vez)

```bash
# 1. Instalar dependencias (si no existe .venv)
cd Ecuador/mcp_web_connector
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Completar credenciales
cp .env.example .env
# Editar .env con usuario SSH y contraseña o llave privada
# MCP_WEB_SSH_USER=root  (o usuario cPanel)
# MCP_WEB_SSH_PASSWORD=tu_contraseña

# 3. Registrar en Claude Code
# Settings → MCP Servers → Add from file → mcp-config.example.json
# O agregar manualmente el bloque de mcp-config.example.json

# 4. Verificar conexión
# Skill: config_summary → debe retornar ssh_host=51.79.104.194
# Skill: ssh_health   → debe retornar hostname y whoami del servidor
```

### Skills disponibles (usar estas, no alternativas directas)

| Skill | Qué hace |
|---|---|
| `config_summary` | Verifica que el .env cargó correctamente |
| `ssh_health` | Prueba SSH y retorna info del servidor (hostname, PHP, disco) |
| `get_server_host_key` | Obtiene la host key del servidor para verificación estricta |
| `remote_list` | Lista archivos de un directorio remoto vía SFTP |
| `remote_read_text` | Lee un archivo de texto del servidor |
| `remote_write_text` | **Escribe/reemplaza un archivo en el servidor** (con backup automático en /tmp) |
| `remote_write_binary` | Sube archivos binarios (imágenes, fuentes) al servidor |
| `remote_deploy_files` | **Despliega múltiples archivos en una sola llamada** |
| `remote_exec` | Ejecuta comandos permitidos (ls, cp, chmod, service reload…) |

### Flujo de deploy estándar

```
1. config_summary   → verificar que .env cargó
2. ssh_health       → confirmar servidor activo
3. remote_list      → ver web root en servidor
4. remote_deploy_files → subir archivos locales modificados
5. remote_list      → confirmar que los archivos llegaron
```

### Lo que está PROHIBIDO hacer directamente

```
✗  ssh root@51.79.104.194  (sin MCP)
✗  sftp / scp / rsync directos al servidor
✗  FTP con FileZilla u otro cliente
✗  cPanel File Manager manual
✗  curl/wget para escribir en el servidor
✗  Cualquier acceso a /etc/shadow, /root, .env de producción
```

### Verificación inicial obligatoria

Antes de cualquier tarea que involucre el servidor, ejecutar:

```json
{ "name": "config_summary" }
```

Si falla (error de conexión), revisar `.env` y reportar al usuario.

---

## Estructura

```
Ecuador/
├── CLAUDE.md                              ← Este archivo (instrucciones para IA)
├── RELEASE.md                             ← Historial de versiones
├── index.html                             ← Home del sitio público
├── style.css                              ← Estilos globales del sitio
├── sitemap.xml                            ← Sitemap de producción
├── .htaccess                              ← Reglas Apache (no modificar sin rev.)
│
├── mcp_web_connector/                     ← MCP local (PUNTO DE ENTRADA OBLIGATORIO)
│   ├── server.py                          ← Servidor MCP v0.1.0 (stdio, JSON-RPC 2.0)
│   ├── requirements.txt                   ← paramiko, sshtunnel, pymysql
│   ├── .env                               ← Credenciales reales (NO en git)
│   ├── .env.example                       ← Template de .env
│   ├── mcp-config.example.json            ← Config para Claude Code
│   ├── README.md                          ← Instalación, skills y flujo de deploy
│   └── .venv/                             ← Entorno virtual Python (local, no en git)
│
├── internet-corporativo-ecuador.html      ← ✅ SEO — creada 2026-05-28
├── internet-dedicado-ecuador.html         ← ✅ SEO — creada 2026-05-28
├── canales-de-datos-ecuador.html          ← ✅ SEO — creada 2026-05-28
├── fibra-optica-empresas-ecuador.html     ← ✅ SEO — creada 2026-05-28
│
├── soluciones.html
├── soluciones/
│   ├── connection.html
│   ├── cloud.html
│   ├── collaboration.html
│   └── security.html
│
├── cobertura.html
├── contactanos.html
├── quienes-somos.html
├── asesoramiento.html
├── asesoramiento/
│   ├── informacion-tecnica.html
│   ├── preguntas-frecuentes.html
│   ├── seguridad.html
│   └── tips-de-seguridad.html
│
├── normas-y-regulaciones.html
├── normatividad-y-regulaciones/
│   ├── derechos-de-los-abonados.html
│   └── reglamentos-del-consumidor.html
│
├── pqrs.html / preguntas-frecuentes.html / velocimetro.html
├── encuesta-de-satisfaccion.html / gracias.html (noindex)
│
├── css/                                   ← Estilos externos (Jarvis, FancyBox)
├── js/                                    ← Scripts del sitio público
├── fonts/
├── images/
│   ├── controls/                          ← Logos, íconos, nav, footer
│   ├── custom/                            ← Imágenes por página
│   └── system/                            ← Favicons, manifest, og/
│
├── php/                                   ← Formularios PHP (contacto, pqrs, encuesta)
│   └── library/secretKey.php             ← reCAPTCHA key Ecuador
├── logs/
└── seo/                                   ← Auditorías SEO
    └── auditoria-seo-2026-05-23.md
```

---

## Páginas SEO creadas (2026-05-28)

Cuatro páginas de aterrizaje para keywords de conectividad B2B en Ecuador.
El nav de TODAS las páginas del sitio fue actualizado para incluirlas.

| Página | Keywords principales | Schema |
|---|---|---|
| `internet-corporativo-ecuador.html` | internet corporativo Ecuador, SLA 99.9% | Service + WebPage + FAQPage |
| `internet-dedicado-ecuador.html` | internet dedicado Ecuador, fibra óptica dedicada | Service + WebPage + FAQPage |
| `canales-de-datos-ecuador.html` | canales de datos Ecuador, MPLS Ecuador | Service + WebPage + FAQPage |
| `fibra-optica-empresas-ecuador.html` | fibra óptica empresas Ecuador, FTTB | Service + WebPage + FAQPage |

### Nav section 3 — estado actual (todas las páginas)

```html
<li><a href="internet-corporativo-ecuador.html">Internet Corporativo</a></li>
<li><a href="internet-dedicado-ecuador.html">Internet Dedicado</a></li>
<li><a href="canales-de-datos-ecuador.html">Canales de Datos</a></li>
<li><a href="fibra-optica-empresas-ecuador.html">Fibra Óptica Empresas</a></li>
<li><a href="cobertura.html">Cobertura</a></li>
<li><a href="velocimetro.html">Velocímetro</a></li>
<li><a href="normas-y-regulaciones.html">Normas y regulaciones</a></li>
<li><a href="asesoramiento.html">Asesoramiento</a></li>
```

Subdirectorios usan `../` en los hrefs. El script Python de actualización masiva está documentado en el historial de commits.

---

## Diferencias clave Ecuador vs. Perú

| Aspecto | Ecuador | Perú |
|---|---|---|
| Dominio | `mediacommerce.ec` | `mcperu.pe` |
| MCP ID | `mcecuador-web` | `mcperu-web` |
| IP servidor | `51.79.104.194` | `179.43.82.54` |
| Email | `servicioalcliente@mediacommerce.ec` | `ventas@mcperu.pe` |
| Regulador | ARCOTEL | OSIPTEL |
| Moneda | USD | PEN |
| Ciudad referencia | Quito | Lima |
| WhatsApp | `593987592186` | `51971244843` |
| Facebook | `MediaCommerceOficial` | link distinto |
| LinkedIn | `media-commerce-partners-s.a/` | `media-commerceperu/` |
| Instagram | **No existe** | Sí |
| Módulo Ordenes | **No existe** | Sí (`ordenes/`) |
| Blog | **No existe** | Sí (`blog/`) |
| Base de datos | **No configurada** | MariaDB `bdmcperu` |
| Panel cPanel | `https://51.79.104.194:2083/` | N/A (VPS) |

---

## Flujo de trabajo

1. **Edición local:** modificar archivos en `Ecuador/` con las herramientas de Claude Code.
2. **Deploy:** usar MCP `mcecuador-web` skill `remote_deploy_files`.
3. **Verificación:** `remote_list` para confirmar que los archivos llegaron al servidor.
4. **Git:** hacer commit después del deploy exitoso.

### Ejemplo de deploy con MCP

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

> Reemplazar `<usuario>` con el usuario cPanel real del servidor (verificar con `ssh_health` o `remote_list /home`).

---

## Tareas pendientes

- [ ] **Completar `.env` del MCP** con usuario y contraseña SSH de `51.79.104.194` para activar el deploy automatizado
- [ ] **Verificar web root** con `remote_list /home` para confirmar el usuario cPanel
- [ ] **Hacer primer deploy** de las 4 páginas SEO + nav actualizado al servidor
- [ ] **Añadir las 4 páginas al `sitemap.xml`** de Ecuador
- [ ] **Crear imagen OG** `images/system/og/og-connection.jpg` (1200×630px)
- [ ] **Auditoría SEO** de las 4 páginas nuevas (Lighthouse, Core Web Vitals)

---

## Notas técnicas

- El CSS/JS de cada página SEO está `<style>` inline en el `<head>` — mismo patrón que Perú.
- El accordion FAQ usa JavaScript vanilla, sin jQuery.
- El botón flotante de WhatsApp apunta siempre a `593987592186` — **nunca al número de Perú**.
- El footer siempre usa ARCOTEL — **nunca OSIPTEL ni INDECOPI**.
- El `.venv/` del MCP está en `.gitignore` — cada desarrollador lo instala localmente.

*Última actualización: 2026-05-28 — MCP obligatorio documentado, 4 páginas SEO desplegadas localmente*
