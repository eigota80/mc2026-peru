# Playbook SEO para WordPress

## Revisión inicial

- Identificar CMS, tema, builder y plugin SEO si son visibles o provistos por el usuario.
- Revisar si existen sitemaps duplicados: WordPress core, Yoast, Rank Math, All in One SEO u otros.
- Confirmar que las páginas importantes tengan titles, metas, canonicals y schema consistentes.
- Revisar si categorías, etiquetas, autores, archivos de fecha, adjuntos o búsquedas internas están indexándose sin valor.

## Problemas frecuentes

### Parámetros y páginas antiguas

WordPress puede conservar URLs como `?p=123`, `?page_id=456`, archivos de autor, categorías o adjuntos. Si aparecen en buscadores y duplican páginas limpias:

- redirigir 301 hacia la URL limpia cuando exista equivalente.
- devolver 410 cuando sea contenido eliminado sin reemplazo.
- agregar canonical correcto solo cuando la página duplicada deba permanecer accesible.
- limpiar enlaces internos que apunten a parámetros.

### Indexación no deseada

Evaluar `noindex` para:

- resultados de búsqueda interna.
- páginas de autor sin valor diferencial.
- etiquetas de baja calidad.
- categorías vacías o duplicadas.
- adjuntos individuales.
- páginas de prueba, staging o thank-you pages.

No usar robots.txt como único método para retirar contenido ya indexado. Si una página ya está indexada, verificar eliminación, redirección, 410 o noindex según corresponda.

### Señales de posible compromiso

Escalar como crítico si hay:

- páginas indexadas sobre casino, fármacos, apuestas, esteroides, descargas, contenido adulto o idiomas ajenos al sitio.
- archivos PHP sospechosos dentro de temas, uploads o plugins.
- URLs extrañas bajo `/wp-content/`, `/wp-includes/`, `sale.php`, `index.php?`, parámetros largos o rutas no relacionadas.
- usuarios administradores desconocidos.
- redirecciones solo para bots o visitantes móviles.

Plan de contención recomendado:

1. Revisar usuarios administradores y accesos FTP/SFTP/hosting.
2. Actualizar core, plugins y temas.
3. Eliminar archivos maliciosos y reinstalar componentes desde fuentes oficiales.
4. Cambiar contraseñas y claves salting.
5. Revisar Search Console: acciones manuales, problemas de seguridad, cobertura e historial.
6. Devolver 410 o 301 para URLs spam según corresponda.
7. Solicitar retirada temporal solo como contención; luego resolver la causa y confirmar desindexación.

## Plugins SEO

No depender del plugin como solución única. Verificar la salida HTML real:

- title final.
- meta robots.
- canonical.
- schema.
- sitemap.
- Open Graph si es relevante.
- breadcrumbs.

## Rendimiento WordPress

- revisar hosting, caché de página, object cache, CDN, compresión de imágenes, lazy loading, fuentes, scripts de terceros y builder pesado.
- optimizar primero plantillas de mayor impacto: home, landings, categorías, producto/servicio y posts con tráfico.
