# Auditoria SEO - Media Commerce Ecuador

**Fecha:** 2026-05-23  
**Dominio auditado:** https://www.mediacommerce.ec  
**Mercado:** Ecuador - B2B Telecomunicaciones  
**Alcance:** 26 URLs en `sitemap.xml`, paginas HTML publicas principales, duplicados canonicos, `service-worker.js`, `.htaccess` y recursos SEO visibles en codigo.

---

## Resumen ejecutivo

| Categoria | Estado |
|---|---|
| Titles presentes | [OK] 26/26 paginas publicas |
| Meta descriptions presentes | [OK] 26/26 paginas publicas |
| Canonical tags | [ALERTA] 2 problemas criticos y varias inconsistencias |
| H1 | [ALERTA] `index.html` tiene 2 H1; `asesoramiento.html` y `normas-y-regulaciones.html` no tienen H1 |
| Open Graph / Twitter | [ALERTA] faltan `og:image` y `twitter:image` en todas las paginas |
| JSON-LD Schema | [CRITICO] 0/26 paginas publicas tienen datos estructurados |
| `robots.txt` | [CRITICO] no existe en la raiz de Ecuador |
| `sitemap.xml` | [ALERTA] incluye URLs que no deberian indexarse y duplicados no canonicos |
| Paginas de confirmacion | [CRITICO] `gracias.html` y `encuesta-de-satisfaccion.html` estan en sitemap y sin `noindex` |
| Enlaces internos | [OK] sin enlaces internos rotos detectados |
| Imagenes publicas | [OK] 85/85 imagenes HTML tienen `alt` |
| GTM | [ALERTA] falta en 2 paginas normativas |

**Puntuacion SEO tecnica estimada:** 58/100

El sitio tiene una base util: titles, descriptions, canonicals y enlaces internos existen en la mayoria de paginas. El principal problema es de indexabilidad y enriquecimiento semantico: falta `robots.txt`, el sitemap envia senales contradictorias, no hay datos estructurados y hay paginas no comerciales expuestas a indexacion.

---

## Hallazgos prioritarios

### 1. Falta `robots.txt` en Ecuador

**Estado:** Critico  
**Evidencia:** `find . -maxdepth 3 -name 'robots.txt'` solo encontro `Peru/robots.txt`.  
**Impacto:** Los rastreadores no reciben reglas explicitas para rutas internas como `/logs/`, `/php/`, `/_deploy/`, `/error/`, ni la ubicacion del sitemap de Ecuador.

**Recomendacion:** crear `robots.txt` en la raiz:

```txt
User-agent: *
Allow: /

Disallow: /logs/
Disallow: /php/
Disallow: /_deploy/
Disallow: /error/
Disallow: /Ecuador/
Disallow: /*.sql$
Disallow: /*.env$

Sitemap: https://www.mediacommerce.ec/sitemap.xml
```

> Nota: para excluir paginas HTML de resultados, usar `noindex`; `robots.txt` sirve para controlar rastreo, no como mecanismo principal de desindexacion.

---

### 2. Sitemap mezcla URLs canonicas, duplicadas y paginas que no deberian posicionar

**Estado:** Critico  
**Archivo:** `sitemap.xml`  
**URLs actuales:** 26  

**Problemas detectados:**

| URL en sitemap | Problema |
|---|---|
| `/gracias.html` | Pagina de confirmacion, no deberia indexarse |
| `/encuesta-de-satisfaccion.html` | Pagina transaccional, no deberia indexarse |
| `/informacion-tecnica.html` | Canonical apunta a `/asesoramiento/informacion-tecnica.html` |
| `/preguntas-frecuentes.html` | Canonical apunta a `/asesoramiento/preguntas-frecuentes.html` |
| `/seguridad.html` | Canonical apunta a `/asesoramiento/seguridad.html` |
| `/tips-de-seguridad.html` | Canonical apunta a `/asesoramiento/tips-de-seguridad.html` |

**Impacto:** Google recibe senales mezcladas: el sitemap sugiere indexar URLs que sus propios canonicals consolidan en otras paginas. Esto puede desperdiciar rastreo y debilitar consolidacion.

**Recomendacion:** dejar el sitemap solo con URLs canonicas e indexables. Excluir confirmaciones, duplicados legacy y plantillas.

---

### 3. Canonicals con errores

| Pagina | Canonical actual | Problema | Recomendacion |
|---|---|---|---|
| `gracias.html` | `https://www.mediacommerce.ecgracias.html` | URL mal formada, falta `/` | `https://www.mediacommerce.ec/gracias.html` y agregar `noindex,follow` |
| `velocimetro.html` | `https://www.mediacommerce.ec/test-de-velocidad.html` | Apunta a una URL que no existe en el proyecto | Cambiar a `https://www.mediacommerce.ec/velocimetro.html` o crear redireccion real |
| `index.html` | `https://www.mediacommerce.ec` | Inconsistente con sitemap (`/`) | Usar `https://www.mediacommerce.ec/` |

---

### 4. `gracias.html` y `encuesta-de-satisfaccion.html` estan indexables

**Estado:** Critico  
**Problema:** Ambas estan en `sitemap.xml`, tienen canonical propio y no tienen `<meta name="robots" content="noindex,follow">`.

**Impacto:** Pueden aparecer en resultados de busqueda aunque no sean landings de adquisicion. Tambien pueden crear resultados de baja calidad.

**Recomendacion:**

```html
<meta name="robots" content="noindex,follow">
```

Y retirarlas del sitemap.

---

### 5. No hay datos estructurados JSON-LD

**Estado:** Critico  
**Evidencia:** 0 bloques `application/ld+json` en las 26 paginas publicas.  
**Impacto:** Se pierde contexto semantico para organizacion, servicios, breadcrumbs, FAQ, contacto y paginas corporativas.

**Schemas recomendados:**

| Pagina | Schema recomendado |
|---|---|
| `index.html` | `Organization`, `WebSite`, `WebPage` |
| `soluciones.html` | `CollectionPage`, `BreadcrumbList` |
| `soluciones/connection.html` | `Service`, `BreadcrumbList` |
| `soluciones/cloud.html` | `Service`, `BreadcrumbList` |
| `soluciones/collaboration.html` | `Service`, `BreadcrumbList` |
| `soluciones/security.html` | `Service`, `BreadcrumbList` |
| `contactanos.html` | `ContactPage`, `LocalBusiness` |
| `pqrs.html` | `ContactPage` |
| `asesoramiento/preguntas-frecuentes.html` | `FAQPage`, `BreadcrumbList` |
| `velocimetro.html` | `WebApplication` |
| Normatividad | `WebPage`, `BreadcrumbList` |

**Prioridad:** empezar por home, soluciones, contacto y FAQs.

---

### 6. Faltan imagenes sociales `og:image` y `twitter:image`

**Estado:** Alto  
**Evidencia:** todas las paginas publicas tienen `og:title` y `og:description`, pero ninguna tiene `og:image` ni `twitter:image`.

**Impacto:** Al compartir en WhatsApp, LinkedIn, Facebook o X, las tarjetas pueden renderizarse sin imagen o con una imagen escogida automaticamente.

**Recomendacion:** crear una imagen social 1200x630 para Ecuador, por ejemplo:

```html
<meta property="og:image" content="https://www.mediacommerce.ec/images/system/og/og-share-ecuador.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:image" content="https://www.mediacommerce.ec/images/system/og/og-share-ecuador.jpg">
```

---

### 7. Jerarquia H1 inconsistente

**Estado:** Alto

| Pagina | Problema | Recomendacion |
|---|---|---|
| `index.html` | Tiene 2 H1 | Mantener solo el hero como H1; cambiar el segundo a H2 |
| `asesoramiento.html` | No tiene H1, usa H3 principal | Cambiar el titulo visual principal a H1 |
| `normas-y-regulaciones.html` | No tiene H1, usa H3 principal | Cambiar el titulo visual principal a H1 |

---

### 8. Titles y descriptions necesitan optimizacion comercial

**Estado:** Medio  
**Patron:** muchos titles son muy genericos: `Cloud | Media Commerce ®`, `Security | Media Commerce ®`, `PQRSF | Media Commerce ®`, `Cobertura | Media Commerce ®`.

**Recomendaciones por prioridad:**

| Pagina | Title sugerido |
|---|---|
| `soluciones/connection.html` | Conectividad empresarial en Ecuador \| Media Commerce |
| `soluciones/cloud.html` | Soluciones Cloud para empresas en Ecuador \| Media Commerce |
| `soluciones/security.html` | Seguridad informatica empresarial en Ecuador \| Media Commerce |
| `soluciones/collaboration.html` | Colaboracion digital para empresas en Ecuador \| Media Commerce |
| `cobertura.html` | Cobertura de red empresarial en Ecuador \| Media Commerce |
| `pqrs.html` | PQRSF y atencion al cliente \| Media Commerce Ecuador |

**Errores de copy detectados:**

- `Concejos de seguridad` deberia ser `Consejos de seguridad`.
- `soluciones/collaboration.html` contiene `tecnologíá`; deberia ser `tecnologia`.
- Varias descriptions son demasiado cortas, por ejemplo 50-54 caracteres en asesoramiento/seguridad/tips/FAQ.

---

### 9. Falta GTM en paginas normativas

**Estado:** Medio  
**Paginas sin `GTM-N4SCNV2`:**

- `normatividad-y-regulaciones/derechos-de-los-abonados.html`
- `normatividad-y-regulaciones/reglamentos-del-consumidor.html`

**Impacto:** esas paginas no quedarian medidas con la misma consistencia que el resto del sitio.

---

### 10. Oportunidad de contenido SEO para Ecuador

**Estado:** Alto  
**Comparacion interna:** Peru tiene landings y blog orientados a busqueda (`internet-dedicado-peru.html`, `internet-corporativo-peru.html`, `fibra-optica-empresas-peru.html`, `canales-de-datos-peru.html`, `blog/`). Ecuador no tiene equivalentes.

**Impacto:** El sitio Ecuador depende de paginas de marca y categoria, pero tiene poca superficie para busquedas transaccionales como:

- internet dedicado empresas Ecuador
- fibra optica empresarial Ecuador
- internet corporativo Ecuador
- conectividad empresarial Ecuador
- ciberseguridad empresarial Ecuador
- soluciones cloud empresas Ecuador

**Recomendacion:** crear 4 landings comerciales y 6 articulos base, adaptados a Ecuador, no copiados literalmente desde Peru.

---

## Metadatos por pagina

| Pagina | Title chars | Description chars | H1 | JSON-LD | Nota |
|---|---:|---:|---:|---:|---|
| `index.html` | 66 | 156 | 2 | 0 | Title largo y 2 H1 |
| `asesoramiento.html` | 32 | 133 | 0 | 0 | Falta H1 |
| `normas-y-regulaciones.html` | 40 | 110 | 0 | 0 | Falta H1 |
| `gracias.html` | 27 | 89 | 1 | 0 | Canonical roto, deberia ser noindex |
| `encuesta-de-satisfaccion.html` | 43 | 90 | 1 | 0 | Deberia ser noindex |
| `velocimetro.html` | 30 | 78 | 1 | 0 | Canonical apunta a URL inexistente |
| `soluciones.html` | 42 | 173 | 1 | 0 | Description algo larga |
| `soluciones/cloud.html` | 24 | 103 | 1 | 0 | Title generico |
| `soluciones/connection.html` | 29 | 111 | 1 | 0 | Title generico |
| `soluciones/security.html` | 27 | 126 | 1 | 0 | Title generico |
| `soluciones/collaboration.html` | 32 | 140 | 1 | 0 | Title generico |
| `asesoramiento/preguntas-frecuentes.html` | 39 | 54 | 1 | 0 | Description corta |
| `asesoramiento/seguridad.html` | 36 | 50 | 1 | 0 | Description corta |
| `asesoramiento/tips-de-seguridad.html` | 40 | 50 | 1 | 0 | Typo en title, description corta |
| `contactanos.html` | 30 | 118 | 1 | 0 | Title generico |
| `pqrs.html` | 24 | 141 | 1 | 0 | Title generico |

---

## Fortalezas detectadas

- Todas las paginas publicas tienen `lang="es"`, `charset` y viewport responsive.
- No se detectaron enlaces internos rotos entre paginas HTML publicas.
- Las 85 imagenes referenciadas en HTML publico tienen `alt`.
- La mayoria de paginas tienen canonical declarado.
- Existe GTM en la mayoria del sitio.
- Hay versiones WebP y mobile/tablet en varias imagenes clave, especialmente en secciones visuales nuevas.

---

## Plan de accion recomendado

### Prioridad 1 - Indexabilidad

1. Crear `robots.txt` para Ecuador.
2. Corregir canonicals de `gracias.html`, `velocimetro.html` e `index.html`.
3. Agregar `noindex,follow` a `gracias.html` y `encuesta-de-satisfaccion.html`.
4. Regenerar `sitemap.xml` solo con URLs canonicas indexables.

### Prioridad 2 - Semantica y CTR

1. Crear imagen OG/Twitter para Ecuador.
2. Agregar `og:image` y `twitter:image` a todas las paginas.
3. Agregar JSON-LD en home, servicios, contacto, FAQ y breadcrumbs.
4. Ajustar H1 en `index.html`, `asesoramiento.html` y `normas-y-regulaciones.html`.

### Prioridad 3 - Contenido organico

1. Reescribir titles y descriptions de servicios con intencion comercial Ecuador.
2. Crear landings de internet dedicado, fibra optica, internet corporativo y canales de datos.
3. Crear blog B2B Ecuador con articulos de conectividad, cloud, colaboracion y seguridad.
4. Conectar esas landings desde home, soluciones y footer.

---

## Referencias usadas

- Google Search Central: Sitemaps y URLs canonicas en sitemap: https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
- Google Search Central: Canonicalizacion y duplicados: https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
- Google Search Central: robots.txt y limites de uso: https://developers.google.com/search/docs/crawling-indexing/robots/intro
- Google Search Central: meta descriptions y snippets: https://developers.google.com/search/docs/appearance/snippet
- Google Search Central: datos estructurados: https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data
