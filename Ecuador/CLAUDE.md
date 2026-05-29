# CLAUDE.md — Proyecto MC Ecuador 2026

> **Regla de oro: toda IA que trabaje en este proyecto DEBE usar el MCP `mcecuador-web` para cualquier acceso, modificación o deploy al servidor de producción. El acceso directo vía SSH, FTP, cPanel File Manager o cualquier otro método NO está permitido.**

---

## Índice

1. [Identidad del proyecto](#identidad)
2. [MCP Obligatorio — regla principal](#mcp-obligatorio)
3. [Cómo hacer deploy — paso a paso](#deploy)
4. [Estructura del proyecto](#estructura)
5. [Páginas SEO en producción](#paginas-seo)
6. [Diferencias Ecuador vs. Perú](#diferencias)
7. [Tareas pendientes](#pendientes)

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

**Ninguna IA puede acceder ni modificar el servidor Ecuador sin pasar por el MCP `mcecuador-web`.**

### Datos reales del servidor (confirmados en producción)

| Parámetro | Valor |
|---|---|
| **Hostname** | `hc-02.webserver.ec` |
| **IP** | `51.79.106.41` |
| **Puerto SSH** | `22` |
| **Usuario SSH** | `mediaco2` |
| **Llave privada** | `~/.ssh/mc2026/mcecuador-mediaco2-rsa` |
| **Web root** | `/home/mediaco2/public_html/` |
| **Tipo hosting** | cPanel (Apache) |
| **cPanel** | `https://hc-02.webserver.ec:2083/` |
| **Estado** | ✅ Conectado y verificado 2026-05-28 |

### Configuración del MCP

| Parámetro | Valor |
|---|---|
| Servidor Python | `Ecuador/mcp_web_connector/server.py` |
| Protocolo | stdio JSON-RPC 2.0 (MCP 2024-11-05) |
| ID en Claude Code | `mcecuador-web` |
| Config Claude Code | `Ecuador/mcp_web_connector/mcp-config.example.json` |
| Credenciales | `Ecuador/mcp_web_connector/.env` |
| venv | `Ecuador/mcp_web_connector/.venv/` |

### Lo que está PROHIBIDO hacer directamente

```
✗  ssh mediaco2@hc-02.webserver.ec  (sin MCP)
✗  sftp / scp / rsync directos al servidor
✗  FTP con FileZilla u otro cliente
✗  cPanel File Manager manual
✗  curl/wget para escribir en el servidor
```

---

## Deploy — Cómo actualizar el sitio

### Verificación inicial (ejecutar SIEMPRE primero)

```json
{ "name": "config_summary" }
```
Debe retornar `ssh_host: "hc-02.webserver.ec"`. Si falla, revisar `.env`.

```json
{ "name": "ssh_health" }
```
Confirma que el servidor está activo. Retorna hostname, PHP, disco.

### Ver archivos actuales en el servidor

```json
{
  "name": "remote_list",
  "arguments": {
    "path": "/home/mediaco2/public_html",
    "max_entries": 100
  }
}
```

### Subir UN archivo

```json
{
  "name": "remote_write_text",
  "arguments": {
    "path": "/home/mediaco2/public_html/nombre-del-archivo.html",
    "content": "<contenido completo del archivo HTML>"
  }
}
```
Hace backup automático del archivo anterior en `/tmp/mcp_backup/` antes de sobreescribir.

### Subir MÚLTIPLES archivos (deploy batch)

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

### Verificar que los archivos llegaron

```json
{
  "name": "remote_list",
  "arguments": {
    "path": "/home/mediaco2/public_html",
    "max_entries": 100
  }
}
```

### Leer un archivo del servidor (para comparar)

```json
{
  "name": "remote_read_text",
  "arguments": {
    "path": "/home/mediaco2/public_html/index.html"
  }
}
```

### Flujo completo recomendado

```
1. config_summary      → verificar que .env cargó
2. ssh_health          → confirmar servidor activo
3. remote_list         → ver estado actual
4. [editar archivos localmente]
5. remote_deploy_files → subir archivos modificados
6. remote_list         → confirmar que llegaron
7. git commit          → guardar en repositorio
```

---

## Estructura del proyecto

```
Ecuador/
├── CLAUDE.md                              ← Este archivo (leer antes de trabajar)
├── RELEASE.md                             ← Historial de versiones
├── index.html                             ← Home del sitio
├── style.css                              ← Estilos globales
├── sitemap.xml                            ← Sitemap de producción
├── .htaccess                              ← Reglas Apache
│
├── mcp_web_connector/                     ← ⚠️ PUNTO DE ENTRADA OBLIGATORIO
│   ├── server.py                          ← Servidor MCP v0.1.0
│   ├── .env                               ← Credenciales reales (NO en git)
│   ├── .env.example                       ← Template
│   ├── mcp-config.example.json            ← Config para Claude Code
│   ├── requirements.txt                   ← paramiko, sshtunnel, pymysql
│   ├── README.md                          ← Documentación detallada del MCP
│   └── .venv/                             ← Entorno virtual Python (no en git)
│
├── internet-corporativo-ecuador.html      ← ✅ SEO producción 2026-05-28
├── internet-dedicado-ecuador.html         ← ✅ SEO producción 2026-05-28
├── canales-de-datos-ecuador.html          ← ✅ SEO producción 2026-05-28
├── fibra-optica-empresas-ecuador.html     ← ✅ SEO producción 2026-05-28
│
├── soluciones.html / soluciones/          ← cloud, connection, collaboration, security
├── cobertura.html / contactanos.html
├── quienes-somos.html / asesoramiento.html / asesoramiento/
├── normas-y-regulaciones.html / normatividad-y-regulaciones/
├── pqrs.html / preguntas-frecuentes.html
├── velocimetro.html / seguridad.html
├── tips-de-seguridad.html / informacion-tecnica.html
├── encuesta-de-satisfaccion.html / gracias.html (noindex)
│
├── css/ js/ fonts/ images/ php/ logs/ error/
└── seo/auditoria-seo-2026-05-23.md
```

---

## Páginas SEO en producción

Estado actual del servidor `www.mediacommerce.ec`:

| Página | URL producción | HTTP | Fecha deploy |
|---|---|---|---|
| Internet Corporativo | `/internet-corporativo-ecuador.html` | 200 ✅ | 2026-05-28 |
| Internet Dedicado | `/internet-dedicado-ecuador.html` | 200 ✅ | 2026-05-28 |
| Canales de Datos | `/canales-de-datos-ecuador.html` | 200 ✅ | 2026-05-28 |
| Fibra Óptica Empresas | `/fibra-optica-empresas-ecuador.html` | 200 ✅ | 2026-05-28 |

**Total páginas en servidor:** 31 HTML (27 originales + 4 SEO nuevas)

### Nav global — estado actual (todas las páginas)

Sección 3 del menú en páginas raíz:
```html
<li><a href="internet-corporativo-ecuador.html" class="mainNav-btn">Internet Corporativo</a></li>
<li><a href="internet-dedicado-ecuador.html" class="mainNav-btn">Internet Dedicado</a></li>
<li><a href="canales-de-datos-ecuador.html" class="mainNav-btn">Canales de Datos</a></li>
<li><a href="fibra-optica-empresas-ecuador.html" class="mainNav-btn">Fibra Óptica Empresas</a></li>
<li><a href="cobertura.html" class="mainNav-btn">Cobertura</a></li>
<li><a href="velocimetro.html" class="mainNav-btn">Velocímetro</a></li>
<li><a href="normas-y-regulaciones.html" class="mainNav-btn">Normas y regulaciones</a></li>
<li><a href="asesoramiento.html" class="mainNav-btn">Asesoramiento</a></li>
```
En subdirectorios (`asesoramiento/`, `soluciones/`, `normatividad-y-regulaciones/`) los hrefs llevan `../`.

---

## Diferencias clave Ecuador vs. Perú

| Aspecto | Ecuador | Perú |
|---|---|---|
| Dominio | `mediacommerce.ec` | `mcperu.pe` |
| MCP ID | `mcecuador-web` | `mcperu-web` |
| SSH host | `hc-02.webserver.ec` | `179.43.82.54` |
| SSH user | `mediaco2` | `mcp-agent` / `root` |
| Llave SSH | `~/.ssh/mc2026/mcecuador-mediaco2-rsa` | `~/.ssh/mc2026/mcp-agent-mcperu` |
| Web root | `/home/mediaco2/public_html/` | `/var/www/html/` |
| Email | `servicioalcliente@mediacommerce.ec` | `ventas@mcperu.pe` |
| WhatsApp | `593987592186` | `51971244843` |
| Regulador | **ARCOTEL** | OSIPTEL |
| Moneda | **USD** | PEN |
| Ciudad | **Quito** | Lima |
| Facebook | `MediaCommerceOficial` | distinto |
| Instagram | **No existe** | Sí |
| Módulo Ordenes | **No existe** | Sí |
| Blog | **No existe** | Sí |
| BD MariaDB | **No configurada** | `bdmcperu` |

---

## Tareas pendientes

- [ ] Actualizar `sitemap.xml` con las 4 páginas SEO nuevas y hacer deploy
- [ ] Crear imagen OG `images/system/og/og-connection.jpg` (1200×630px) y hacer deploy
- [ ] Auditoría SEO de las 4 páginas nuevas (Lighthouse, Core Web Vitals)
- [ ] Agregar host key del servidor en `MCP_WEB_SSH_KNOWN_HOST_KEY` del `.env` para verificación estricta

---

## Notas técnicas importantes

- **WhatsApp flotante**: siempre `593987592186` — nunca usar el número de Perú.
- **Footer**: siempre ARCOTEL — nunca OSIPTEL ni INDECOPI.
- **Estilos CSS**: inline en `<style>` dentro de cada página SEO — mismo patrón que Perú.
- **`.venv/`**: no está en git — instalar localmente con `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.
- **IPv4**: el servidor también responde en IPv6, pero el MCP conecta correctamente vía hostname.

*Última actualización: 2026-05-28 — Deploy exitoso, 4 páginas SEO en producción, MCP operativo*
