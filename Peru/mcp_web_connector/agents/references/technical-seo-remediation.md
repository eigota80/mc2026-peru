# technical seo remediation

## indexación y limpieza

Si aparecen urls basura, spam, parámetros, archivos de tema, autores/categorías sin valor o contenido hackeado:

1. validar si la url responde 200, 3xx, 4xx o 5xx.
2. identificar patrón: parámetros, ids antiguos, taxonomías, búsqueda interna, archivos, inyección.
3. si es hackeo o spam, escalar a seguridad antes de seo.
4. eliminar contenido y devolver 410 cuando no exista reemplazo.
5. redirigir 301 solo si hay equivalente real y relevante.
6. usar noindex para páginas accesibles pero no indexables.
7. actualizar sitemap para dejar solo urls canónicas.
8. solicitar recrawl o retirada temporal cuando sea necesario.

No usar robots.txt como única solución para sacar urls ya indexadas.

## canonicals

Usar canonical para consolidar duplicados muy similares cuando todas las versiones deben permanecer accesibles. No usar canonical como sustituto de redirecciones cuando una url antigua ya no debe existir.

Buenas prácticas:

- canonical absoluto.
- autocanonical en páginas finales.
- evitar canonicals contradictorios con noindex, redirects o sitemap.
- no canonicalizar páginas con intención distinta.

## redirecciones

Usar 301 para cambios permanentes de url. Evitar cadenas y bucles. Validar:

- origen responde 301 directo.
- destino responde 200.
- destino es equivalente o mejor.
- enlaces internos se actualizan al destino final.
- sitemap solo incluye destino final.

## robots.txt y sitemap

robots.txt controla rastreo, no garantiza desindexación. Sitemap debe incluir solo urls canónicas, indexables, con 200 y relevantes.

Validar:

- sitemap declarado en robots si conviene.
- sitemap no contiene 3xx, 4xx, noindex, canonicals a otra url ni parámetros innecesarios.
- robots no bloquea css/js necesarios para renderizado.

## performance

Priorizar móvil. Diagnosticar por plantilla, no solo por url individual:

- imágenes sin compresión o dimensiones excesivas.
- javascript bloqueante o de terceros.
- css no usado.
- fuentes pesadas.
- lazy loading mal aplicado.
- servidor lento o ttfb alto.
- sliders, videos o embeds innecesarios en hero.

Recomendar acciones por impacto: optimizar imágenes, cache, cdn, reducir js, preload crítico, diferir terceros, mejorar hosting si corresponde.

## schema

Implementar schema solo cuando represente contenido visible y real. Validar con herramientas oficiales cuando sea posible.

Mapeo común:

- home: organization, website.
- negocio local: localbusiness o subtipo apropiado.
- servicio: service con provider.
- blog: article/blogposting.
- navegación: breadcrumblist.
- preguntas visibles: faqpage.
- productos: product con ofertas reales.

Evitar schema de reseñas si no hay reseñas visibles, legítimas y asociadas al objeto correcto.
