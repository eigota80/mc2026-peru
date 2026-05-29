# CLAUDE.md — Proyecto MC Ecuador 2026

> **Regla de oro: toda IA que trabaje en este proyecto DEBE usar el MCP `mcecuador-web` para cualquier acceso, modificación o deploy al servidor de producción. El acceso directo vía SSH, FTP, cPanel File Manager o cualquier otro método NO está permitido.**

---

## Índice

1. [Identidad del proyecto](#identidad)
2. [MCP Obligatorio — cómo conectarse y hacer deploy](#mcp-obligatorio)
3. [Estado actual en producción](#estado-produccion)
4. [Cómo actualizar el sitio — paso a paso](#como-actualizar)
5. [Estructura del proyecto](#estructura)
6. [Diferencias Ecuador vs. Perú](#diferencias)
7. [Tareas pendientes](#pendientes)

---

## Identidad

| Parámetro | Valor |
|---|---|
| **Dominio** | `https://www.mediacommerce.ec` |
| **Mercado** | Ecuador — B2B — Telecomunicaciones, conectividad, cloud, seguridad |
| **Idioma** | Español, variante Ecuador (`es-EC`) |
| **Moneda JSON-LD** | USD |
| **Regulador telecom** | ARCOTEL (`http://www.arcotel.gob.ec/`) |
| **GTM** | `GTM-N4SCNV2` |
| **GA4** | `G-5GEKHX28YV` (implementado 2026-05-28 en 30 páginas) |

### Contacto

| Canal | Dato |
|---|---|
| Email | `servicioalcliente@mediacommerce.ec` |
| Teléfono fijo | `+593 (2) 394 2280 A 2289` |
| Línea gratuita | `01 800 633 423` |
| Celular | `+593 98 759 2186` / `+593 98 786 1855` |
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

### Datos de conexión (confirmados en producción)

| Parámetro | Valor |
|---|---|
| **Hostname** | `hc-02.webserver.ec` |
| **IP** | `51.79.106.41` |
| **Puerto SSH** | `22` |
| **Usuario** | `mediaco2` |
| **Llave privada** | `~/.ssh/mc2026/mcecuador-mediaco2-rsa` |
| **Web root** | `/home/mediaco2/public_html/` |
| **Tipo** | cPanel (Apache) |
| **cPanel** | `https://hc-02.webserver.ec:2083/` |

### Registrar el MCP en Claude Code

Agregar en `~/.claude/settings.json`:

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

### Skills disponibles

| Skill | Para qué |
|---|---|
| `config_summary` | Verificar que el .env cargó — **ejecutar siempre primero** |
| `ssh_health` | Confirmar que el servidor está activo |
| `remote_list` | Ver archivos en el servidor |
| `remote_read_text` | Leer un archivo del servidor |
| `remote_write_text` | Escribir/reemplazar un archivo (backup automático) |
| `remote_write_binary` | Subir imágenes, fuentes, binarios |
| `remote_deploy_files` | Deploy masivo — múltiples archivos a la vez |
| `remote_exec` | Comandos seguros post-deploy (chmod, ls, service reload) |

### Lo que está PROHIBIDO

```
✗  ssh mediaco2@hc-02.webserver.ec  (sin MCP)
✗  sftp / scp / rsync / FTP directos
✗  cPanel File Manager manual
✗  curl/wget para escribir en el servidor
```

---

## Estado actual en producción

**Última actualización:** 2026-05-28  
**Total páginas:** 31 HTML + robots.txt + sitemap.xml

### Medición y analytics

| Herramienta | ID | Estado |
|---|---|---|
| Google Tag Manager | `GTM-N4SCNV2` | ✅ Activo en todas las páginas |
| Google Analytics 4 | `G-5GEKHX28YV` | ✅ Activo en 30 páginas (implementado 2026-05-28) |

### SEO técnico

| Elemento | Estado |
|---|---|
| `robots.txt` | ✅ Creado 2026-05-28 |
| `sitemap.xml` | ✅ 24 URLs, actualizado 2026-05-28 |
| `og:image` + `twitter:image` | ✅ En todas las páginas (apuntan a `og-share-ecuador.jpg`) |
| JSON-LD `index.html` | ✅ Organization + WebSite + WebPage |
| JSON-LD páginas SEO | ✅ Service + WebPage + FAQPage (4 páginas) |
| H1 correcto en todos | ✅ Corregidos `index.html`, `asesoramiento.html`, `normas-y-regulaciones.html` |
| Canonicals | ✅ Corregidos `gracias.html`, `velocimetro.html`, `index.html` |
| `noindex` en páginas de confirmación | ✅ `gracias.html` y `encuesta-de-satisfaccion.html` |
| Titles con keyword Ecuador | ✅ 6 páginas de servicios |
| GTM en todas | ✅ Incluyendo normatividad (faltaba) |

### Páginas SEO en producción (HTTP 200)

| Página | URL | Deploy |
|---|---|---|
| Internet Corporativo | `/internet-corporativo-ecuador.html` | ✅ 2026-05-28 |
| Internet Dedicado | `/internet-dedicado-ecuador.html` | ✅ 2026-05-28 |
| Canales de Datos | `/canales-de-datos-ecuador.html` | ✅ 2026-05-28 |
| Fibra Óptica Empresas | `/fibra-optica-empresas-ecuador.html` | ✅ 2026-05-28 |

---

## Cómo actualizar el sitio

### Flujo completo para cualquier agente

```
1. Editar archivos localmente en Ecuador/
2. Verificar MCP:       config_summary
3. Confirmar servidor:  ssh_health
4. Subir archivos:      remote_deploy_files
5. Verificar deploy:    remote_list /home/mediaco2/public_html
6. Commit git
```

### Verificar conexión MCP

```json
{ "name": "config_summary" }
```
Debe retornar `ssh_host: "hc-02.webserver.ec"`. Si falla, revisar `.env`.

### Ver archivos en el servidor

```json
{
  "name": "remote_list",
  "arguments": { "path": "/home/mediaco2/public_html", "max_entries": 100 }
}
```

### Subir un archivo

```json
{
  "name": "remote_write_text",
  "arguments": {
    "path": "/home/mediaco2/public_html/nombre-archivo.html",
    "content": "<!-- contenido completo del archivo -->"
  }
}
```

### Deploy de múltiples archivos (recomendado)

```json
{
  "name": "remote_deploy_files",
  "arguments": {
    "files_json": "[
      {\"local\": \"/Users/eidergonzaleztamara/Documents/web side/MC_2026/Ecuador/index.html\",
       \"remote\": \"/home/mediaco2/public_html/index.html\"},
      {\"local\": \"/Users/eidergonzaleztamara/Documents/web side/MC_2026/Ecuador/soluciones.html\",
       \"remote\": \"/home/mediaco2/public_html/soluciones.html\"}
    ]"
  }
}
```

### Subir imagen o archivo binario

```json
{
  "name": "remote_write_binary",
  "arguments": {
    "path": "/home/mediaco2/public_html/images/system/og/og-share-ecuador.jpg",
    "local_path": "/Users/eidergonzaleztamara/Documents/web side/MC_2026/Ecuador/images/system/og/og-share-ecuador.jpg"
  }
}
```

### Leer un archivo del servidor

```json
{
  "name": "remote_read_text",
  "arguments": { "path": "/home/mediaco2/public_html/index.html" }
}
```

---

## Reglas para nuevas páginas

Al crear cualquier página nueva para Ecuador, DEBE incluir:

```html
<!-- 1. GA4 — al inicio de <head> -->
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-5GEKHX28YV"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-5GEKHX28YV');
</script>

<!-- 2. og:image (después de twitter:description) -->
<meta property="og:image" content="https://www.mediacommerce.ec/images/system/og/og-share-ecuador.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Media Commerce Ecuador">
<meta name="twitter:image" content="https://www.mediacommerce.ec/images/system/og/og-share-ecuador.jpg">

<!-- 3. GTM (antes de </head>) -->
<script>(function(w,d,s,l,i){...GTM-N4SCNV2...})</script>

<!-- 4. JSON-LD apropiado al tipo de página -->
<script type="application/ld+json">{ ... }</script>

<!-- 5. Un solo H1 visible en el contenido -->
```

Y en el nav (sección 3), incluir:
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
En subdirectorios, los hrefs llevan `../`.

Después de crear la página, agregarla al `sitemap.xml` y hacer deploy de ambos archivos.

---

## Estructura del proyecto

```
Ecuador/
├── CLAUDE.md                              ← Este archivo — leer antes de trabajar
├── robots.txt                             ← ✅ Creado 2026-05-28
├── sitemap.xml                            ← ✅ 24 URLs, actualizado 2026-05-28
├── .htaccess                              ← Reglas Apache
├── style.css                              ← Estilos globales
│
├── mcp_web_connector/                     ← ⚠️ ÚNICO PUNTO DE ENTRADA AL SERVIDOR
│   ├── server.py                          ← MCP v0.1.0
│   ├── .env                               ← Credenciales reales (NO en git)
│   ├── .env.example                       ← Template
│   ├── mcp-config.example.json            ← Config para Claude Code
│   ├── requirements.txt
│   ├── README.md                          ← Documentación detallada del MCP
│   └── .venv/                             ← Instalar con: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
│
├── internet-corporativo-ecuador.html      ← ✅ SEO + GA4 + JSON-LD
├── internet-dedicado-ecuador.html         ← ✅ SEO + GA4 + JSON-LD
├── canales-de-datos-ecuador.html          ← ✅ SEO + GA4 + JSON-LD
├── fibra-optica-empresas-ecuador.html     ← ✅ SEO + GA4 + JSON-LD
│
├── index.html                             ← ✅ GA4 + JSON-LD Org + H1 corregido
├── soluciones.html / soluciones/          ← ✅ GA4 + og:image + titles Ecuador
├── cobertura.html / contactanos.html      ← ✅ GA4 + og:image
├── quienes-somos.html / asesoramiento.html← ✅ GA4 + og:image + H1
├── asesoramiento/                         ← ✅ GA4 + og:image
├── normas-y-regulaciones.html             ← ✅ GA4 + og:image + H1
├── normatividad-y-regulaciones/           ← ✅ GA4 + GTM (faltaba) + og:image
├── pqrs.html / preguntas-frecuentes.html  ← ✅ GA4 + og:image
├── velocimetro.html                       ← ✅ GA4 + canonical corregido
├── gracias.html / encuesta-de-satisfaccion.html ← ✅ noindex,follow
│
├── css/ js/ fonts/ images/ php/ logs/ error/
└── seo/auditoria-seo-2026-05-23.md
```

---

## Diferencias clave Ecuador vs. Perú

| Aspecto | Ecuador | Perú |
|---|---|---|
| Dominio | `mediacommerce.ec` | `mcperu.pe` |
| MCP ID | `mcecuador-web` | `mcperu-web` |
| SSH host | `hc-02.webserver.ec` | `179.43.82.54` |
| SSH user | `mediaco2` | `mcp-agent` / `root` |
| Llave SSH | `mcecuador-mediaco2-rsa` | `mcp-agent-mcperu` |
| Web root | `/home/mediaco2/public_html/` | `/var/www/html/` |
| GA4 | `G-5GEKHX28YV` | `G-R4PVGLZDS8` |
| GTM | `GTM-N4SCNV2` (compartido) | `GTM-N4SCNV2` (compartido) |
| Email | `servicioalcliente@mediacommerce.ec` | `ventas@mcperu.pe` |
| WhatsApp | `593987592186` | `51971244843` |
| Regulador | **ARCOTEL** | OSIPTEL |
| Moneda | **USD** | PEN |
| Ciudad | **Quito** | Lima |
| Instagram | **No existe** | Sí |
| Módulo Ordenes | **No existe** | Sí |
| Blog | **No existe** | Sí |
| BD MariaDB | **No configurada** | `bdmcperu` |

---

## Tareas pendientes

- [ ] Crear imagen OG `images/system/og/og-share-ecuador.jpg` (1200×630px) — todas las páginas ya la referencian, falta el archivo físico
- [ ] Agregar blog B2B Ecuador (conectividad, cloud, ciberseguridad, colaboración)
- [ ] JSON-LD en páginas restantes: `soluciones/connection.html`, `contactanos.html`, `asesoramiento/preguntas-frecuentes.html`
- [ ] Descriptions más largas en asesoramiento/seguridad, tips, FAQ (actualmente 50-54 chars)

---

## Notas importantes para cualquier agente

- **GA4 `G-5GEKHX28YV`** va al inicio de `<head>` en TODAS las páginas.
- **WhatsApp flotante** apunta siempre a `593987592186` — nunca al de Perú.
- **Footer**: siempre ARCOTEL — nunca OSIPTEL ni INDECOPI.
- **Imagen OG**: `og-share-ecuador.jpg` — el archivo aún no existe, pero todas las páginas ya apuntan a él.
- **CSS**: estilos inline en `<style>` en páginas SEO — mismo patrón que Perú.
- **`.venv/`**: no está en git — instalar localmente con `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.

*Última actualización: 2026-05-28 — GA4 implementado, auditoría SEO completada, 31 páginas en producción*
