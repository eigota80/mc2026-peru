# CLAUDE.md — Proyecto MC Peru 2026

> **Regla de oro: toda IA que trabaje en este proyecto DEBE usar el MCP `mcperu-web` para cualquier acceso al servidor remoto o a la base de datos. El acceso directo via SSH, SCP, FTP o cliente de base de datos externo NO está permitido.**

---

## Indice

1. [Identidad del proyecto](#identidad)
2. [Estado actual del sistema](#estado-actual)
3. [Regla de uso exclusivo del MCP](#mcp-obligatorio)
4. [Estructura del proyecto](#estructura)
5. [Módulo Ordenes de Servicio](#ordenes-de-servicio)
6. [Módulo SEO y sitio público](#seo-y-sitio-publico)
7. [API PHP backend](#api-php)
8. [Seguridad y produccion](#seguridad)
9. [Flujo de trabajo y deploy](#flujo-de-trabajo)
10. [Referencias clave](#referencias)

---

## Identidad

- **Dominio canónico:** `https://www.mcperu.pe`
- **Mercado:** Peru — B2B — Telecomunicaciones, conectividad, cloud, seguridad empresarial
- **Idioma:** español, variante Peru
- **Servidor de producción:** `179.43.82.54` (Apache, MariaDB `bdmcperu`)
- **Repositorio:** rama principal `main`, rama activa según contexto

---

## Estado actual

> Última actualización: 2026-05-29

### MCP connector

| Parametro | Valor |
|---|---|
| Estado | **Operativo** |
| Llave SSH activa | `mcp_web_connector/id_rsa` (RSA 4096, con passphrase en `.env`) |
| Usuario SSH | `mcp-agent` |
| Usuario BD activo | `root` (temporal hasta crear `mcp_agent_ro` con script `03-setup-db-user.sh`) |
| Fix aplicado | Stub `paramiko.DSSKey` en `server.py` para compatibilidad con paramiko 5.x |

### Base de datos `bdmcperu`

| Detalle | Valor |
|---|---|
| Tablas totales | 69 (WordPress + tablas custom) |
| Tabla de órdenes | `orden_servicio` — 23 columnas |
| Campo consecutivo | `numero_os` VARCHAR(10) — UNIQUE KEY |
| Máximo `numero_os` | `000703` (4 registros totales) |
| Estados activos | `Creada` (3), `Facturacion validada` (1) |
| Soft-delete | **No implementado** — pendiente Fase 2 |

### Procedimiento obligatorio para cualquier agente al iniciar

```
1. Verificar MCP: ejecutar config_summary.
   Si falla → detener y reportar al usuario. No continuar.

2. Si la tarea involucra la BD: ejecutar mysql_list_tables para confirmar acceso.

3. Para leer archivos del servidor: usar remote_list y remote_read_text.

4. Para cambios en el sitio: editar localmente → branch → PR → merge → CI/CD.

5. NUNCA ejecutar INSERT/UPDATE/DELETE/ALTER via MCP ni directamente.
```

---

## MCP Obligatorio

**Ninguna IA puede acceder al servidor ni a la base de datos sin pasar por el MCP.**

### Configuración del servidor MCP

| Parámetro | Valor |
|---|---|
| Servidor | `mcp_web_connector/server.py` |
| Protocolo | stdio JSON-RPC 2.0 (MCP 2024-11-05) |
| ID en Claude Code | `mcperu-web` |
| Config de ejemplo | `mcp_web_connector/mcp-config.example.json` |

### Skills disponibles (usar estas, no alternativas directas)

| Skill | Qué hace |
|---|---|
| `config_summary` | Verifica que el agente cargó bien el `.env` |
| `ssh_health` | Diagnóstica conectividad SSH y versiones del servidor |
| `remote_list` | Lista archivos en el servidor remoto |
| `remote_read_text` | Lee archivos remotos (límite 50 000 bytes) |
| `mysql_query_readonly` | Ejecuta SELECT/SHOW/DESCRIBE en `bdmcperu` |
| `mysql_list_tables` | Lista tablas de la base de datos |
| `mysql_describe_table` | Describe columnas de una tabla |
| `wordpress_users` | Busca usuarios en `wp_users` |
| `wordpress_options` | Lee opciones de `wp_options` |
| `find_client_columns` | Detecta columnas de clientes/contactos |
| `export_result_json` | Ejecuta SELECT y retorna JSON listo para copiar |

El catálogo completo con parámetros y ejemplos está en [`mcp_web_connector/SKILLS.md`](mcp_web_connector/SKILLS.md).

### Lo que está PROHIBIDO hacer directamente

```
✗  ssh user@179.43.82.54 (sin MCP)
✗  scp / rsync directos al servidor
✗  Cliente MySQL / DBeaver / TablePlus sin MCP
✗  curl/wget para escribir en el servidor
✗  Cualquier acceso a /etc/shadow, /root, .env de producción
✗  INSERT/UPDATE/DELETE vía MCP (solo SELECT está habilitado)
```

### Verificación inicial obligatoria

Antes de cualquier tarea que involucre el servidor o la BD, ejecutar:

```json
{ "name": "config_summary" }
```

Si falla, detener y reportar al usuario.

---

## Estructura

```
Peru/
├── CLAUDE.md                    ← Este archivo (instrucciones para IA)
├── AGENTS.md                    ← Instrucciones de agentes (SEO, seguridad)
├── index.html                   ← Home del sitio público
├── style.css                    ← Estilos globales del sitio
├── sitemap.xml                  ← Sitemap de producción
├── robots.txt                   ← Directivas de rastreo
├── service-worker.js            ← PWA cache
│
├── css/                         ← Estilos externos (Jarvis, FancyBox, Color)
├── js/                          ← Scripts externos del sitio público
├── fonts/                       ← Tipografías locales
├── images/                      ← Imágenes del sitio
│   ├── controls/                ← Logos, íconos, nav, footer
│   ├── custom/                  ← Imágenes por página (index/, no-index/)
│   └── system/                  ← Favicons, app-icons, manifest
├── error/                       ← Páginas de error personalizadas
│
├── ordenes/                     ← Panel interno (NUNCA indexar en sitemap)
│   ├── ordenes-servicio.html    ← Vista principal de órdenes
│   ├── ordenes-servicio.js      ← Lógica principal del módulo
│   ├── ordenes-servicio.css     ← Estilos del panel
│   ├── login.js
│   ├── dashboard.html
│   ├── cotizaciones.html
│   ├── Clientes.html
│   ├── usuarios.html
│   ├── auditoria.html
│   ├── informes.html
│   ├── importar-clientes.html   ← Herramienta interna de importación
│   ├── importar-ordenes.html
│   ├── importar-cotizaciones.html
│   └── backend/                 ← Backend Python experimental (local)
│       ├── app.py
│       └── db.py
│
├── api/                         ← Backend PHP REST (producción en Apache)
│   ├── config.php               ← Conexión MariaDB
│   ├── ordenes.php
│   ├── cotizaciones.php
│   └── clientes.php
│
├── database/                    ← Schemas SQL de referencia
│   ├── ordenes_servicio_schema.sql
│   └── mariadb_schema.sql
│
├── php/                         ← Scripts PHP de formularios públicos
│   ├── contacto/send.php
│   ├── encuesta/send.php
│   ├── pqrs/send.php
│   ├── library/                 ← PHPMailer y dependencias
│   ├── templates/               ← Plantillas HTML de email
│   └── logs/
│
├── logs/                        ← Datos de formularios (CSV) y auditoría local
│   └── account/data/            ← contacto.csv, encuesta, pqrs, segmento
│
├── mcp_web_connector/           ← MCP local (PUNTO DE ENTRADA OBLIGATORIO)
│   ├── server.py                ← Servidor MCP (stdio, JSON-RPC 2.0)
│   ├── SKILLS.md                ← Catálogo completo de skills
│   ├── README.md                ← Instalación, seguridad y flujo de deploy
│   ├── .env                     ← Credenciales (NO en git)
│   ├── mcp-config.example.json  ← Config de ejemplo para Claude Code
│   ├── requirements.txt
│   ├── .venv/                   ← Entorno virtual Python
│   ├── agents/                  ← Skills de agentes especializados
│   │   ├── SKILL.md             ← Skill SEO especialista
│   │   ├── openai.yaml          ← Config agente OpenAI
│   │   ├── references/          ← Referencias SEO (checklists, latam, remediation)
│   │   └── scripts/             ← Scripts Python de análisis SEO
│   └── scripts/                 ← Scripts de configuración del servidor remoto
│
├── seo/                         ← Auditorías y estrategia de backlinks
│   ├── auditoria-seo-2026-05-21.md
│   └── backlinks/
│
├── MenuBar/                     ← CSS de componente MenuBar (legado)
│
├── blog/                        ← Artículos del blog público
├── asesoramiento/               ← Subpáginas de asesoramiento
├── soluciones/                  ← Subpáginas de soluciones
├── normatividad-y-regulaciones/ ← Subpáginas regulatorias
│
└── [páginas HTML públicas]      ← index, soluciones, cobertura, contactanos, etc.
```

---

## Ordenes de Servicio

- Módulo interno accesible solo por usuarios autenticados.
- Datos de órdenes en MariaDB (`orden_servicio`) **y** en `localStorage` del navegador.
- El consecutivo `numero_os` se genera actualmente en `localStorage` (riesgo de desincronización — Fase 2 lo centralizará en backend PHP).
- Cotizaciones y clientes en MariaDB (`bdmcperu`): tablas `cotizacion`, `cotizacion_detalle`, `empresa`.
- **No incluir ninguna URL de `ordenes/` en `sitemap.xml`.**
- **Mantener `noindex,nofollow`** en todas las páginas del panel.
- Consultas a la BD solo via MCP skill `mysql_query_readonly`.
- Escritura en BD requiere endpoint PHP + `F-04 mysql_write` en MCP (ver SKILLS.md).

### Tablas principales en `bdmcperu`

| Tabla | Descripción |
|---|---|
| `orden_servicio` | Órdenes de servicio — campo clave `numero_os` (UNIQUE), max `000703` |
| `empresa` | Clientes / razones sociales, RUC, contactos |
| `cotizacion` | Cabecera de cotizaciones |
| `cotizacion_detalle` | Líneas de cada cotización |

### Columnas de `orden_servicio`

`id`, `numero_os`, `razon_social`, `ruc_dni`, `fecha`, `moneda`, `duracion`,
`tipo_servicio`, `ciudad`, `dias_entrega`, `direccion_origen`, `direccion_destino`,
`detalle`, `servicio`, `mrc`, `costo_instalacion`, `nrc`, `observacion`,
`facilidades_pago`, `estado`, `created_by`, `created_at`, `updated_at`

> Sin `deleted_at`/`deleted_by` — soft-delete pendiente de Fase 2.

---

## SEO y Sitio Público

- Cargar primero el skill local en `mcp_web_connector/agents/SKILL.md` para tareas SEO.
- Referencias disponibles en `mcp_web_connector/agents/references/`:
  - `seo-checklists.md` — auditorías técnicas y on-page
  - `spanish-latam-seo.md` — copy SEO en español Peru/LatAm
  - `technical-seo-remediation.md` — robots, canonicals, redirects, schema
  - `output-templates.md` — reportes y planes 30/60/90

### Reglas del sitemap

- Solo páginas públicas con contenido real.
- Excluir: panel Ordenes, gracias.html, encuesta-de-satisfaccion.html, API, PHP, logs, backups, importar-*.html.

---

## API PHP

- Endpoints en `api/`: `ordenes.php`, `cotizaciones.php`, `clientes.php`
- Configuración de conexión en `api/config.php` (credenciales en `.env` local, no en git)
- Las consultas desde agentes IA van vía MCP, no llamando directamente a los endpoints PHP

---

## Seguridad

- Nunca leer ni modificar `.env`, backups, credenciales ni archivos fuera de las raíces permitidas.
- Las consultas SQL via MCP son de **solo lectura** (`SELECT`, `SHOW`, `DESCRIBE`, `EXPLAIN`).
- El usuario del servidor es `mcp-agent` con clave SSH RSA 4096, sin acceso root.
- Historial de accesos en `/var/log/mcp-agent/` en el servidor remoto.
- Variables sensibles **nunca en git**: SSH key, DB password, tokens de CI/CD.

---

## Flujo de Trabajo

1. **Diagnóstico**: ejecutar `config_summary` y `ssh_health` vía MCP.
2. **Lectura remota**: usar `remote_list` y `remote_read_text` para inspeccionar producción.
3. **Datos**: usar `mysql_query_readonly` o skills especializadas para consultar la BD.
4. **Edición**: editar archivos localmente con las herramientas de Claude Code.
5. **Deploy**: via Git — branch → PR → merge → GitHub Actions → producción.
6. No hacer deploy manual sin pasar por el flujo de PR documentado en `mcp_web_connector/README.md`.

---

## Referencias

| Recurso | Ruta |
|---|---|
| Catálogo de skills MCP | [`mcp_web_connector/SKILLS.md`](mcp_web_connector/SKILLS.md) |
| Instalación y deploy | [`mcp_web_connector/README.md`](mcp_web_connector/README.md) |
| Instrucciones de agentes | [`AGENTS.md`](AGENTS.md) |
| Skill SEO | [`mcp_web_connector/agents/SKILL.md`](mcp_web_connector/agents/SKILL.md) |
| Schema de BD | [`database/ordenes_servicio_schema.sql`](database/ordenes_servicio_schema.sql) |
| Config MCP ejemplo | [`mcp_web_connector/mcp-config.example.json`](mcp_web_connector/mcp-config.example.json) |

---

*Última actualización: 2026-05-29 — Fix MCP (paramiko 5.x), estado BD Fase 1, procedimiento de agente documentado*
