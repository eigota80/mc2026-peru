# Marco de auditoria SEO

## Alcance recomendado

Una auditoria SEO completa debe cubrir siete capas:

1. Indexacion y seguridad
2. Rastreo y arquitectura tecnica
3. Relevancia on-page
4. Contenido e intencion de busqueda
5. Experiencia, performance y conversion
6. Autoridad, reputacion y enlaces
7. Medicion, gobierno y seguimiento

No todas las capas tienen el mismo peso. Para un sitio con problemas de indexacion o spam, resolver eso pesa mas que optimizar textos. Para un sitio sano pero estancado, contenido, autoridad y conversion pueden pesar mas.

## Puntuacion base sugerida

Usar una escala 0 a 100. Ajustar pesos segun el objetivo del usuario.

- Indexacion, seguridad y duplicacion: 20 puntos
- SEO tecnico y rastreo: 20 puntos
- On-page y arquitectura semantica: 20 puntos
- Contenido, intencion y autoridad tematica: 15 puntos
- Performance, mobile y UX de conversion: 10 puntos
- Autoridad externa y reputacion: 10 puntos
- Medicion y gobierno SEO: 5 puntos

Interpretacion:

- 85 a 100: base solida, foco en crecimiento y refinamiento.
- 70 a 84: buen potencial, hay brechas tacticas o tecnicas.
- 50 a 69: sitio vulnerable, requiere plan de correccion priorizado.
- 30 a 49: problemas fuertes que limitan indexacion, relevancia o confianza.
- 0 a 29: riesgo critico; atender seguridad, rastreo o arquitectura antes de contenido.

## Modelo de severidad

### Critico

Asignar cuando el problema puede:

- impedir que Google rastree o indexe paginas importantes;
- exponer contenido hackeado, spam o malware;
- provocar acciones manuales o problemas de seguridad;
- generar duplicacion masiva o canonicals incorrectos en paginas de negocio;
- romper conversiones organicas principales;
- afectar una migracion o redisenio en produccion.

### Alto

Asignar cuando el problema:

- afecta URLs con valor comercial;
- provoca canibalizacion entre paginas importantes;
- degrada fuerte el CTR por titles/metas deficientes;
- reduce performance movil de paginas clave;
- impide que una pagina satisfaga la intencion principal;
- crea una mala arquitectura de enlaces internos.

### Medio

Asignar cuando el problema:

- mejora relevancia, profundidad, enlazado o claridad;
- afecta paginas secundarias;
- representa una oportunidad de contenido o schema;
- requiere optimizacion, pero no bloquea indexacion o conversion.

### Bajo

Asignar cuando el problema:

- es cosmetico o de consistencia;
- afecta metadatos secundarios;
- tiene impacto bajo o incierto;
- se puede resolver despues de las prioridades comerciales.

## Matriz de prioridad

Calcular prioridad con cinco variables:

- Severidad: critico 5, alto 4, medio 3, bajo 1
- Impacto: 1 a 5 segun trafico, leads, ingresos, indexacion o riesgo
- Esfuerzo: 1 a 5, donde 1 es facil y 5 es complejo
- Confianza: 1 a 5 segun evidencia disponible
- Dependencia: 1 a 5, donde 5 significa que desbloquea otras tareas

Formula sugerida:

`score = ((severidad * 2) + (impacto * 2) + confianza + dependencia) / esfuerzo`

Ordenar de mayor a menor. No usar la formula de forma ciega: un issue critico de seguridad o indexacion siempre va arriba aunque su esfuerzo sea alto.

## Evidencia minima por hallazgo

Cada hallazgo importante debe incluir por lo menos una evidencia:

- URL afectada;
- captura o texto observado;
- resultado de busqueda;
- codigo de estado;
- directiva robots/noindex/canonical;
- pagina competidora;
- dato de Search Console/Analytics;
- fuente oficial;
- patron reproducible.

Si no hay evidencia suficiente, marcar como hipotesis y proponer la validacion.

## Orden de correccion recomendado

1. Seguridad, spam, malware y contenido inyectado.
2. Bloqueos de rastreo/indexacion, noindex incorrectos, robots, canonicals y redirects.
3. Duplicacion masiva, parametros, facetas y URLs obsoletas.
4. Paginas comerciales principales: titles, H1, contenido, CTAs, schema y enlaces internos.
5. Arquitectura, clusters tematicos y contenido faltante.
6. Performance movil y UX de conversion.
7. Autoridad externa, PR digital y enlaces.
8. Medicion, reporting y mejora continua.
