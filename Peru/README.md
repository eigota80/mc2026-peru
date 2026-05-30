# MC Peru 2026

Proyecto web de Media Commerce Peru. Incluye sitio publico, panel interno de ordenes de servicio, endpoints PHP, referencias SQL y conector MCP para operaciones remotas controladas.

## Entrada Para Agentes

Antes de hacer cambios:

1. Leer `AGENTS.md`.
2. Leer `CLAUDE.md` si la tarea toca arquitectura, produccion, BD o deploy.
3. Leer `ordenes/README.md` si la tarea toca el panel interno.
4. Usar el MCP `mcperu-web` para cualquier acceso al servidor remoto o a MariaDB.

No usar SSH, SCP, FTP ni clientes de BD directos.

## Estructura Principal

| Ruta | Uso |
|---|---|
| `index.html` | Home publica |
| `style.css` | Estilos globales |
| `css/`, `js/`, `images/` | Assets del sitio publico |
| `soluciones/`, `blog/`, `asesoramiento/` | Secciones publicas |
| `ordenes/` | Panel interno no indexable |
| `api/` | Backend PHP |
| `database/` | Schemas y migraciones |
| `php/` | Formularios publicos y emails |
| `mcp_web_connector/` | Conector MCP obligatorio |
| `seo/` | Auditorias y estrategia SEO |

## Desarrollo Local

Desde esta carpeta:

```bash
python3 -m http.server 8001
```

Abrir:

```text
http://127.0.0.1:8001/
http://127.0.0.1:8001/ordenes/
```

Para comprobar que no hay copias duplicadas:

```bash
find "/Users/eidergonzaleztamara/Documents/web side/MC_2026/Peru" -name "* 2*" -print
```

La salida esperada es vacia.

## Reglas De Cambio

- Mantener el dominio canonico `https://www.mcperu.pe`.
- Mantener el mercado Peru, idioma espanol y enfoque B2B.
- No incluir `ordenes/`, APIs, logs, backups ni herramientas internas en `sitemap.xml`.
- Mantener `noindex,nofollow` en paginas internas, de confirmacion o utilidad.
- Actualizar cache-busters `?v=` cuando cambien CSS o JS usados por paginas HTML.
- No tocar secretos, `.env`, llaves, backups ni archivos de produccion desde el workspace.

## Documentacion Clave

- `AGENTS.md`: reglas obligatorias para agentes.
- `CLAUDE.md`: contexto general, seguridad, produccion y estructura.
- `ordenes/README.md`: arquitectura del panel interno.
- `mcp_web_connector/README.md`: uso del conector MCP.
- `mcp_web_connector/SKILLS.md`: catalogo de herramientas MCP.
