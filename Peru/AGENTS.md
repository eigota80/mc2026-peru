# Instrucciones Para Agentes

> **REGLA DE ORO — MCP OBLIGATORIO:** Toda IA que opere en este proyecto debe usar el MCP `mcperu-web` para acceder al servidor remoto o a la base de datos. El acceso directo via SSH, SCP, FTP o cliente de base de datos está terminantemente prohibido. Ver `CLAUDE.md` para la documentación completa.

Estas instrucciones aplican a todo el proyecto `Peru`.

## Inicio Obligatorio Para Cualquier Agente

1. Leer este archivo completo antes de editar.
2. Revisar `CLAUDE.md` para contexto del proyecto, estructura y reglas de produccion.
3. Si la tarea toca `ordenes/`, leer tambien `ordenes/README.md`.
4. Si la tarea toca el servidor remoto o la base de datos, verificar primero el MCP `mcperu-web` con `config_summary`. Si falla, detenerse y reportar.
5. Si la tarea es SEO, cargar primero el skill local en `mcp_web_connector/agents/SKILL.md`.
6. Antes de editar, revisar `git status --short` y no revertir cambios ajenos.

## Mapa Rapido Del Proyecto

- `index.html`, `style.css`, `css/`, `js/`, `images/`: sitio publico.
- `soluciones/`, `blog/`, `asesoramiento/`, `normatividad-y-regulaciones/`: secciones publicas.
- `ordenes/`: panel interno de ordenes, clientes, cotizaciones y usuarios. Mantener fuera de indexacion.
- `api/`: endpoints PHP usados por el panel interno y formularios.
- `database/`: schemas y migraciones SQL de referencia.
- `php/`: formularios publicos, plantillas de email y librerias PHP.
- `mcp_web_connector/`: conector MCP obligatorio para servidor/BD. No tocar secretos.
- `seo/`: auditorias, estrategia y backlinks.

## Flujo De Trabajo Para Cambios Locales

- Mantener los cambios pequenos y cercanos a la tarea.
- Usar `rg` para buscar referencias antes de modificar HTML/CSS/JS compartido.
- Para paginas publicas, conservar `lang="es"`, viewport movil, canonical, metas y assets existentes.
- Para el panel `ordenes/`, conservar `noindex,nofollow`, proteccion de sesion y versionado `?v=` cuando cambie JS/CSS.
- Para endpoints PHP, validar rutas relativas desde produccion (`/var/www/html`) y no hardcodear secretos.
- Para cambios SQL, crear migracion en `database/migrations/` y documentar el flujo seguro; no ejecutar escritura en BD salvo aprobacion explicita y herramienta segura.
- No crear copias con sufijo ` 2`; si aparecen, comparar con el original antes de borrar.

## Validacion Local Recomendada

- Sitio estatico:
  - `python3 -m http.server 8001` desde `Peru/`
  - Revisar `http://127.0.0.1:8001/`
  - Revisar recursos locales con `curl -I` o navegador.
- Duplicados:
  - `find "/Users/eidergonzaleztamara/Documents/web side/MC_2026/Peru" -name "* 2*" -print`
- SEO estatico:
  - `rg -n "<title|meta name=\"description\"|canonical|robots|og:|twitter:" *.html soluciones blog asesoramiento`
  - Validar `sitemap.xml` como XML bien formado si se edita.
- Panel `ordenes/`:
  - Revisar `ordenes/README.md`.
  - Confirmar que HTML carga `ordenes-servicio.css` y `ordenes-servicio.js` con cache-buster vigente.

## Git Y Entrega

- Incluir en el commit solo archivos relacionados con la tarea.
- No incluir `id_rsa.pub`, `.env`, backups, logs sensibles ni archivos temporales.
- Antes de finalizar, reportar:
  - archivos modificados,
  - validaciones ejecutadas,
  - cambios no relacionados que quedaron fuera,
  - si hay servidor local corriendo.
- Si se hace commit, usar mensaje claro y verificar `git log -1 --oneline`.

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
- No desplegar a produccion sin instruccion explicita del usuario. Si se despliega o lee produccion, hacerlo solo via MCP `mcperu-web`.

## Validacion Recomendada

- Para cambios SEO estaticos, revisar con `rg` titles, descriptions, canonicals, robots y rutas del sitemap.
- Validar que `sitemap.xml` sea XML bien formado cuando se edite.
- Si se cambian paginas visibles, revisar que el HTML conserve el idioma `es`, viewport movil y assets existentes.
