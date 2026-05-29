# CLAUDE.md — Proyecto MC Ecuador 2026

> **Regla de oro:** Toda IA que trabaje en este proyecto DEBE respetar la identidad de Ecuador. No copiar datos de Perú (teléfonos, emails, regulador) sin adaptarlos primero.

---

## Identidad del proyecto

| Parámetro | Valor |
|---|---|
| **Dominio canónico** | `https://www.mediacommerce.ec` |
| **Mercado** | Ecuador — B2B — Telecomunicaciones, conectividad, cloud, seguridad |
| **Idioma** | Español, variante Ecuador (`es-EC`) |
| **Moneda** | USD |
| **Regulador telecom** | ARCOTEL (`http://www.arcotel.gob.ec/`) |
| **GTM** | `GTM-N4SCNV2` (compartido con Perú) |
| **GA4** | No configurado (solo GTM) |

---

## Contacto Ecuador

| Canal | Dato |
|---|---|
| Email principal | `servicioalcliente@mediacommerce.ec` |
| Teléfono fijo | `+593 (2) 394 2280 A 2289` |
| Línea gratuita | `01 800 633 423` |
| Celular 1 | `+593 98 759 2186` |
| Celular 2 | `+593 98 786 1855` |
| WhatsApp | `https://wa.me/593987592186` |
| Webmail | `https://webmail.mediacommerce.ec` |

---

## Redes sociales Ecuador

| Red | URL |
|---|---|
| Facebook | `https://www.facebook.com/MediaCommerceOficial` |
| Twitter | `https://twitter.com/media_commerce` |
| LinkedIn | `https://www.linkedin.com/company/media-commerce-partners-s.a/` |
| YouTube | `https://www.youtube.com/channel/UCsE50rQtm2X_JjYHuEFWpmA` |
| Instagram | **No configurado** (Ecuador no tiene, no agregar) |

---

## Estructura de páginas

```
Ecuador/
├── CLAUDE.md                         ← Este archivo
├── RELEASE.md                        ← Historial de versiones
├── index.html                        ← Home del sitio
├── style.css                         ← Estilos globales
├── sitemap.xml                       ← Sitemap (actualizar al añadir páginas)
│
├── internet-corporativo-ecuador.html ← ✅ Creada 2026-05-28
├── internet-dedicado-ecuador.html    ← ✅ Creada 2026-05-28
├── fibra-optica-empresas-ecuador.html← ✅ Creada 2026-05-28
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
├── pqrs.html
├── preguntas-frecuentes.html
├── velocimetro.html
├── encuesta-de-satisfaccion.html
├── gracias.html
├── sumate-al-equipo.html
├── seguridad.html
├── tips-de-seguridad.html
├── informacion-tecnica.html
│
├── css/                              ← Estilos externos
├── js/                               ← Scripts del sitio
├── fonts/
├── images/
│   ├── controls/                     ← Logos, íconos
│   ├── custom/                       ← Imágenes por página
│   └── system/                       ← Favicons, manifest, og/
│
├── php/                              ← Formularios PHP
├── logs/
└── seo/                              ← Auditorías SEO
```

---

## Diferencias clave vs. sitio Perú

| Aspecto | Ecuador | Perú |
|---|---|---|
| Dominio | `mediacommerce.ec` | `mcperu.pe` |
| Email | `servicioalcliente@mediacommerce.ec` | `ventas@mcperu.pe` |
| Regulador | ARCOTEL | OSIPTEL |
| Moneda JSON-LD | USD | PEN |
| Referencia ciudad | Quito | Lima |
| Módulo Ordenes | **No existe** | Sí (`ordenes/`) |
| Blog | **No existe** | Sí (`blog/`) |
| Canales de Datos | **No existe** | Sí (`canales-de-datos-peru.html`) |
| Instagram | **No** | Sí |
| `addressCountry` JSON-LD | EC | PE |
| `inLanguage` | es-EC | es-PE |

---

## Páginas SEO creadas en 2026-05-28

Tres páginas de aterrizaje SEO para keywords de conectividad empresarial en Ecuador:

### 1. `internet-corporativo-ecuador.html`
- **Keywords:** internet corporativo Ecuador, SLA 99.9% Ecuador
- **Secciones:** Hero SLA, SLA explicado (ARCOTEL), ventajas MC, comparativa vs operadores ecuatorianos, planes Business Start/Pro/Max, proceso 3 pasos, FAQ 6 preguntas, CTA
- **Schema:** Service + WebPage + FAQPage

### 2. `internet-dedicado-ecuador.html`
- **Keywords:** internet dedicado Ecuador, fibra óptica dedicada Ecuador
- **Secciones:** Hero speed card, dedicado vs compartido (visual), specs técnicas 6 celdas, 8 casos de uso (POS/SRI adaptado a Ecuador), planes Dedicado Start/Pro/Max, ribbon IP fija, FAQ 6 preguntas, CTA, "También te puede interesar"
- **Schema:** Service + WebPage + FAQPage

### 3. `fibra-optica-empresas-ecuador.html`
- **Keywords:** fibra óptica empresas Ecuador, FTTB Ecuador
- **Secciones:** Hero light beams, fibra vs cobre tabla, mosaic specs 6 celdas (red propia Ecuador), seguridad por sector (banca, salud, gobierno), proceso 4 pasos instalación, 6 casos de uso (financiero/Superintendencia de Bancos), planes Fibra Start/Pro/Max, FAQ DWDM, CTA
- **Schema:** Service + WebPage + FAQPage

---

## Reglas para el nav de las nuevas páginas

Las tres páginas SEO incluyen en el nav (sección 3) los enlaces mutuos:
```html
<li><a href="internet-corporativo-ecuador.html">Internet Corporativo</a></li>
<li><a href="internet-dedicado-ecuador.html">Internet Dedicado</a></li>
<li><a href="fibra-optica-empresas-ecuador.html">Fibra Óptica Empresas</a></li>
<li><a href="cobertura.html">Cobertura</a></li>
<li><a href="velocimetro.html">Velocímetro</a></li>
<li><a href="normas-y-regulaciones.html">Normas y regulaciones</a></li>
<li><a href="asesoramiento.html">Asesoramiento</a></li>
```

---

## Tareas pendientes para futuros agentes

- [ ] **Añadir las 3 páginas al `sitemap.xml`** de Ecuador con `<lastmod>2026-05-28</lastmod>`
- [ ] **Actualizar `index.html`** y `soluciones.html` para enlazar las nuevas páginas desde el nav principal
- [ ] **Crear imágenes OG** en `images/system/og/`: `og-connection.jpg` (1200×630px) — referenciada en las 3 páginas
- [ ] **Crear página `canales-de-datos-ecuador.html`** si se desea paridad con Perú
- [ ] **Auditoría SEO** de las 3 páginas nuevas (Lighthouse, Core Web Vitals)
- [ ] **Deploy** a servidor de producción Ecuador

---

## Notas técnicas

- Las páginas usan el mismo framework CSS/JS que el resto del sitio Ecuador (`css/core.min.css`, `js/core.min.js`, `style.css`)
- Los estilos de cada página están en `<style>` inline dentro del `<head>` — mismo patrón que Perú
- El accordion FAQ usa JavaScript vanilla (no jQuery) — mismo patrón que Perú
- El botón flotante de WhatsApp apunta a `593987592186` — nunca usar el número de Perú (`51971244843`)
- El footer NO incluye INDECOPI ni OSIPTEL — solo ARCOTEL

*Última actualización: 2026-05-28 — Creación de páginas SEO internet corporativo, dedicado y fibra óptica*
