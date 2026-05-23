# Instrucciones Para Agentes

> **REGLA DE ORO — MCP OBLIGATORIO:** Toda IA que opere en este proyecto debe usar el MCP `mcperu-web` para acceder al servidor remoto o a la base de datos. El acceso directo via SSH, SCP, FTP o cliente de base de datos está terminantemente prohibido. Ver `CLAUDE.md` para la documentación completa.

Estas instrucciones aplican a todo el proyecto `Peru`.

## Skill SEO Del Proyecto

- Para cualquier tarea de SEO, contenido, arquitectura, metadatos, indexacion, sitemap, robots, schema, auditoria o mejora de posicionamiento, carga primero el skill local en `mcp_web_connector/agents/SKILL.md`.
- Usa sus referencias solo cuando hagan falta:
  - `mcp_web_connector/agents/references/seo-checklists.md` para auditorias tecnicas y on-page.
  - `mcp_web_connector/agents/references/spanish-latam-seo.md` para copy SEO en espanol de Peru/LatAm.
  - `mcp_web_connector/agents/references/technical-seo-remediation.md` para robots, canonicals, redirects, indexacion, performance y schema.
  - `mcp_web_connector/agents/references/output-templates.md` para reportes, backlogs y planes 30/60/90.
- Mantener como dominio canonico `https://www.mcperu.pe` salvo instruccion explicita en contrario.
- Asumir mercado Peru, idioma espanol y enfoque B2B para telecomunicaciones, conectividad, cloud, colaboracion, seguridad y soporte empresarial.

## Reglas SEO Del Sitio

- Priorizar primero bloqueos de rastreo/indexacion, duplicados, canonicals incorrectos, sitemap desactualizado, paginas internas expuestas, metas genericas y schema no respaldado por contenido visible.
- Las paginas publicas deben tener title unico, meta description orientada al clic, canonical coherente, Open Graph/Twitter basico, un H1 claro y enlaces internos hacia servicios o conversion.
- No incluir en `sitemap.xml` paginas internas, administrativas, de confirmacion, APIs, plantillas PHP, bases de datos, logs, backups ni herramientas de importacion.
- Mantener `noindex,nofollow` en paginas de confirmacion o utilidad como `gracias.html` y `encuesta-de-satisfaccion.html`.
- Mantener fuera de indexacion el panel `ordenes/`, excepto la pagina de login si el negocio decide conservarla publica.
- En contenido para Peru, preferir terminos naturales como proveedor, cotizar, empresas peruanas, cobertura nacional, soporte local, SLA, fibra optica, RUC y sectores empresariales solo cuando apliquen.

## Seguridad Y Produccion

- No usar SSH directo ni credenciales fuera del conector descrito en `mcp_web_connector/SKILLS.md`.
- Las consultas a base de datos deben ser de solo lectura salvo instruccion explicita del usuario y flujo seguro aprobado.
- No tocar secretos, `.env`, backups ni archivos de produccion desde este workspace.

## Validacion Recomendada

- Para cambios SEO estaticos, revisar con `rg` titles, descriptions, canonicals, robots y rutas del sitemap.
- Validar que `sitemap.xml` sea XML bien formado cuando se edite.
- Si se cambian paginas visibles, revisar que el HTML conserve el idioma `es`, viewport movil y assets existentes.
