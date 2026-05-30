# Sistema de Ordenes de Servicio — Media Commerce Peru

Modulo comercial interno. Multi-pagina HTML + CSS + JS. Backend PHP en `api/`. Datos en MariaDB `bdmcperu` y en `localStorage` del navegador.

> **Regla obligatoria:** Todo agente AI accede al servidor y a la BD exclusivamente via el MCP `mcperu-web`.
> Ver instrucciones completas en `Peru/CLAUDE.md` y `Peru/mcp_web_connector/README.md`.

---

## Indice

1. [Estructura de archivos](#estructura-de-archivos)
2. [Arquitectura](#arquitectura)
3. [Flujo de autenticacion](#flujo-de-autenticacion)
4. [Modulos del sistema](#modulos-del-sistema)
5. [Usuarios del sistema](#usuarios-del-sistema)
6. [localStorage — claves](#localstorage--claves)
7. [API PHP — endpoints](#api-php--endpoints)
8. [Base de datos MariaDB](#base-de-datos-mariadb)
9. [Modulo Cotizaciones](#modulo-cotizaciones)
10. [PDF — generacion nativa](#pdf--generacion-nativa)
11. [Reset de datos](#reset-de-datos)
12. [Importacion desde MariaDB](#importacion-desde-mariadb)
13. [Deploy al servidor](#deploy-al-servidor)
14. [Versionado de cache](#versionado-de-cache)
15. [Guia para AI futura](#guia-para-ai-futura)

---

## Estructura de archivos

```
ordenes/
├── ordenes-servicio.html      # Login (pagina de entrada publica)
├── login.js                   # Logica de autenticacion
├── index.html                 # Home — panel de acceso rapido
├── dashboard.html             # Dashboard — metricas y ordenes recientes
├── Clientes.html              # Clientes — busqueda y formulario (capital C en git)
├── ordenes.html               # Ordenes — formulario OS + tabla
├── cotizaciones.html          # Cotizaciones — formulario COT + tabla
├── usuarios.html              # Usuarios — gestion y datos del sistema (admin)
├── auditoria.html             # Auditoria — log de cambios (admin)
├── ordenes-servicio.js        # Todo el JS del sistema
├── ordenes-servicio.css       # Estilos del sistema
├── logo-mc.png                # Logo embebido en PDF como base64
└── README.md                  # Este archivo

api/  (en la raiz Peru/)
├── config.php                 # Conexion PDO a MariaDB
├── ordenes.php                # GET lista OS activas / POST update_status
├── create-order.php           # POST crea OS con consecutivo atomico desde BD
├── delete-order.php           # POST eliminacion logica de OS
├── cotizaciones.php           # GET/POST cotizaciones
└── clientes.php               # GET/POST clientes

database/migrations/
└── 20260529_os_consecutivo_global.sql  # Crea tabla secuencias + columnas soft-delete
```

### Arquitectura multi-pagina

Cada modulo tiene su propio archivo HTML. Todas las paginas:
- Comparten el mismo header, nav y script (`ordenes-servicio.js`)
- Tienen proteccion de sesion: `#appView` esta `hidden` hasta que el JS verifica la sesion
- Usan `<a href="...html">` en el nav (no `<button data-view>`)
- Tienen `is-active` estaticamente en el enlace de su propia pagina

La navegacion entre paginas usa `navigateTo(name)` en JS → `window.location.href`.

---

## Arquitectura

```
Navegador
  ├── localStorage        ← cache local (clientes, cotizaciones, auditoria)
  │                          Las ordenes nuevas se guardan en BD via API
  └── fetch()
        ├── GET  /api/ordenes.php          → lista OS activas desde MariaDB
        ├── POST /api/create-order.php     → crea OS + genera numero_os atomico en BD
        ├── POST /api/delete-order.php     → soft-delete (ELIMINADA + deleted_at)
        ├── POST /api/ordenes.php          → update_status
        └── GET  /api/cotizaciones.php     → cotizaciones historicas

MariaDB bdmcperu
  ├── orden_servicio        ← Ordenes de servicio (000700 en adelante)
  ├── secuencias            ← Tabla de consecutivos atomicos (valor=703 + N creadas)
  ├── cotizacion            ← Cotizaciones historicas (000001-000651)
  ├── cotizacion_detalle
  └── empresa               ← Clientes
```

---

## Flujo de autenticacion

```
ordenes-servicio.html  →  (login valido)  →  index.html
```

- `ordenes-servicio.html`: formulario de login. Si hay sesion activa redirige a `index.html`.
- `index.html`: protegida. Sin sesion activa redirige a `ordenes-servicio.html`.
- Sesion guardada en `mcperu_os_session`.
- Password hasheado con SHA-256 (Web Crypto API) o FNV-1a como fallback.

---

## Modulos del sistema

| Vista | Descripcion | Permiso requerido |
|---|---|---|
| Home | Panel de acceso rapido a todos los modulos | Todos |
| Dashboard | Metricas globales + ordenes recientes | Todos |
| Clientes | Buscar, crear y editar clientes | Todos (editar: `create_clients`) |
| Ordenes | Crear OS + PDF, gestionar estados, borrar | `create_orders` / `update_orders` / `manage_users` |
| Cotizaciones | Crear COT + PDF, historial MariaDB | `create_orders` / `update_orders` |
| Usuarios | Gestion de usuarios, reset de datos | `manage_users` |
| Auditoria | Log de cambios del sistema | `manage_users` |

### Roles y permisos

| Rol | Permisos |
|---|---|
| `administrador` | `create_clients`, `create_orders`, `print_pdf`, `manage_users`, `update_orders`, `validate_billing` |
| `comercial` | `create_clients`, `create_orders`, `print_pdf` |
| `operaciones` | `update_orders`, `print_pdf` |
| `facturacion` | `validate_billing`, `print_pdf` |

---

## Usuarios del sistema

Definidos en `seedUsers` dentro de `ordenes-servicio.js` (linea ~67). Se crean automaticamente al primer inicio.

| Nombre | Email | Rol |
|---|---|---|
| Eider Gonzalez | eider.gonzalez@mcperu.pe | administrador |
| Carol Paredes | carol.paredes@mcperu.pe | administrador |
| Renato Mejia | renato.mejia@mcperu.pe | comercial |
| Jorge Hesse | jorge.hesse@mcperu.pe | comercial |
| Gianpierre Velasquez | gianpierre.velasquez@mcperu.pe | comercial |
| Andres Romero | andres.romero@mcperu.pe | comercial |
| Gene Quispe | gene.quispe@mcperu.pe | comercial |
| Milagros Ravenna | milagros.ravenna@mcperu.pe | comercial |
| Natanael Vargas | natanael.vargas@mcperu.pe | comercial |

Para agregar un usuario: insertar en `seedUsers` y cambiar `USER_SEED_VERSION` a un valor nuevo.

---

## localStorage — claves

| Clave | Contenido | Estado |
|---|---|---|
| `mcperu_os_session` | Sesion activa | Activo |
| `mcperu_os_users` | Usuarios del sistema | Activo |
| `mcperu_os_users_seed_version` | Version del seed de usuarios | Activo |
| `mcperu_os_clients` | Clientes | Activo |
| `mcperu_os_orders` | Cache local de ordenes (refleja BD) | Activo (cache) |
| `mcperu_service_order_next_number` | Consecutivo OS localStorage | **Ignorado** — consecutivo oficial es MariaDB |
| `mcperu_service_order_draft` | Borrador formulario OS | Activo |
| `mcperu_os_cotizaciones` | Cotizaciones | Activo |
| `mcperu_os_cot_next_number` | Consecutivo COT (empieza en 000652) | Activo (COT no migrado aun) |
| `mcperu_os_audit` | Log de auditoria (max 300 entradas) | Activo |
| `mcperu_os_data_version` | Version del reset de datos | Activo |

### Rango de numeracion

- **Cotizaciones historicas (MariaDB)**: 000001 – 000651
- **Ordenes de servicio (MariaDB `secuencias`)**: 000700 en adelante — max actual `000703`
- **Cotizaciones nuevas (localStorage)**: 000652 en adelante

---

## API PHP — endpoints

Todos en `Peru/api/`. Base URL en produccion: `https://www.mcperu.pe/api/`.

| Endpoint | Metodo | Descripcion |
|---|---|---|
| `ordenes.php` | GET | Lista OS activas (`estado <> ELIMINADA AND deleted_at IS NULL`) |
| `ordenes.php` | POST `action=update_status` | Actualiza estado de una OS |
| `create-order.php` | POST | Crea OS con `numero_os` atomico desde `secuencias` |
| `delete-order.php` | POST | Soft-delete (estado=ELIMINADA, deleted_at, deleted_by) |
| `cotizaciones.php` | GET | Lista cotizaciones desde MariaDB |
| `clientes.php` | GET/POST | Clientes desde `empresa` |

### Respuesta de create-order.php (POST)

```json
{ "ok": true, "id": 5, "numero_os": "000704" }
```

### Respuesta de delete-order.php (POST)

```json
{ "ok": true }
```

El `numero_os` borrado queda reservado para siempre — no se reutiliza.

---

## Base de datos MariaDB

Acceso: **solo via MCP** `mcperu-web` con skill `mysql_query_readonly`.

### Tablas del modulo ordenes

| Tabla | Descripcion |
|---|---|
| `orden_servicio` | OS con 25 columnas — ver schema en `database/migrations/` |
| `secuencias` | Consecutivos atomicos. Fila `orden_servicio` con `valor=703+N` |

### Columnas clave de `orden_servicio`

| Columna | Tipo | Descripcion |
|---|---|---|
| `id` | int AUTO_INCREMENT PK | |
| `numero_os` | varchar(10) UNIQUE NOT NULL | Consecutivo tipo `000700` |
| `estado` | varchar(50) DEFAULT 'Creada' | `Creada`, `Instalacion validada`, `Facturacion validada`, `Activada`, `ELIMINADA` |
| `created_by` | varchar(100) | ID de usuario |
| `created_at` | timestamp | Auto |
| `updated_at` | timestamp | Auto ON UPDATE |
| `deleted_at` | datetime NULL | NULL = activa. Fecha si fue borrada logicamente |
| `deleted_by` | varchar(150) NULL | Usuario que borro la orden |

### Tablas historicas (cotizaciones)

| Tabla | Registros | Descripcion |
|---|---|---|
| `empresa` | 450 | Clientes (RUC, razon social, contactos) |
| `cotizacion` | 827 (648 con correlativo) | Cotizaciones historicas |
| `cotizacion_detalle` | 787 | Lineas de servicio por cotizacion |

---

## Modulo Cotizaciones

Pestaña **Cotizaciones** en el nav. Datos en localStorage + historial en MariaDB.

- Crea cotizaciones con multiples lineas de servicio (tabla dinamica)
- PDF automatico al crear ("Cotizacion de Servicio Nro XXXXXX")
- Tabla con filtros por estado y por comercial
- Estados: NUEVA → EN REVISION → APROBADA → CERRADA / ANULADA
- Historial de 647 cotizaciones de MariaDB cargable via pagina importadora

---

## PDF — generacion nativa

PDF generado en JavaScript puro, sin librerias. Motor: `buildPdf()` + `buildServiceOrderContent()` (OS) / `buildCotizacionContent()` (COT).

- Formato A4: 595.276 x 841.89 pt
- Logo embebido como base64 en la constante `LOGO_B64`
- Fuentes: Helvetica (`F1` normal, `F2` bold)
- PDF de cotizacion: hasta 10 lineas de servicio en una pagina

---

## Reset de datos

### Reset automatico (por version)

```javascript
const DATA_VERSION_KEY = 'mcperu_os_data_version';
const DATA_VERSION     = 'reset-20260518-v1';
```

Cuando `DATA_VERSION` no coincide, `resetOrders()` borra ordenes en localStorage y reinicia el consecutivo localStorage a 000700. **El consecutivo oficial en MariaDB no se ve afectado.**

### Reset manual (administrador)

Modulo Usuarios → "Datos del sistema" → boton **Reiniciar ordenes**.

---

## Importacion desde MariaDB

Paginas de importacion disponibles (usar en el mismo navegador del sistema):

| URL en produccion | Funcion |
|---|---|
| `/ordenes/importar-clientes.html` | Importa clientes a localStorage |
| `/ordenes/importar-cotizaciones.html` | Importa cotizaciones historicas |

**Eliminar del servidor despues de usar** via MCP skill `remote_write_text` o peticion al administrador.

---

## Deploy al servidor

Produccion: `https://www.mcperu.pe` → Apache en `/var/www/html/`

### Deploy via MCP (metodo activo)

Usar el MCP `mcperu-web` con skill `remote_write_text` para escribir archivos en `/var/www/html/`.

```
Archivos que cambian frecuentemente:
  Peru/ordenes/ordenes-servicio.js  → /var/www/html/ordenes/ordenes-servicio.js
  Peru/ordenes/ordenes-servicio.css → /var/www/html/ordenes/ordenes-servicio.css
  Peru/api/*.php                    → /var/www/html/api/*.php
```

Siempre actualizar el `?v=` en los HTML antes de deploy.

### Deploy via Git (objetivo)

Branch → PR → merge a `main` → GitHub Actions → produccion automatica.
Funciona cuando `deploy-mcperu.sh` este configurado en el servidor.

### Problema conocido: directorio ordenes en produccion

En el servidor el directorio se llama `ordenes` (minusculas). Verificar que el rsync/deploy use la ruta correcta.

### Clientes.html

El archivo fisico en git es `Clientes.html` (capital C). Al hacer deploy:
```bash
# Via MCP remote_write_text o en el servidor:
cp Clientes.html clientes.html
```

---

## Versionado de cache

```html
<script src="ordenes-servicio.js?v=20260530-backend-v1"></script>
<link rel="stylesheet" href="ordenes-servicio.css?v=20260530-backend-v1">
```

Incrementar el sufijo en cada deploy que modifique JS o CSS. Patron: `YYYYMMDD-descripcion-vN`.

**Version vigente:** `20260530-backend-v1` — Fase 2: consecutivo BD, soft-delete, boton borrar.

---

## Guia para AI futura

> **OBLIGATORIO**: Todo agente AI que trabaje en este proyecto DEBE conectarse al servidor y BD via MCP `mcperu-web`. Las credenciales y llaves SSH estan en `Peru/mcp_web_connector/.env`. El acceso directo via SSH sin MCP no esta permitido.

1. **Backend + localStorage.** Las OS se crean/leen desde MariaDB via `api/`. El localStorage hace de cache. Cotizaciones y clientes aun usan localStorage como fuente primaria.

2. **Consecutivo oficial.** El `numero_os` lo genera `api/create-order.php` desde la tabla `secuencias`. El localStorage key `mcperu_service_order_next_number` esta ignorado para OS; no modificar ni resetear.

3. **Soft-delete.** Borrar una OS marca `estado=ELIMINADA` + `deleted_at` + `deleted_by`. NO hace DELETE fisico. El `numero_os` queda reservado para siempre.

4. **Agregar usuario**: insertar en `seedUsers` + cambiar `USER_SEED_VERSION`.

5. **Forzar reset de ordenes localStorage**: cambiar `DATA_VERSION` (no afecta MariaDB).

6. **Deploy**: usar `remote_write_text` del MCP para PHP y JS/CSS. Actualizar `?v=` en TODOS los HTML. Ver seccion Deploy.

7. **Consultar BD**: usar skill `mysql_query_readonly` del MCP. Solo SELECT/SHOW/DESCRIBE.

8. **Leer archivos del servidor**: `remote_read_text` del MCP. Ruta base `/var/www/html/`.

9. **Cotizaciones vs Ordenes**: modulos separados con claves localStorage y consecutivos distintos. Cotizaciones NO tienen backend de creacion propio aun.

10. **El PDF** usa logo base64 en `LOGO_B64`. No usa canvas (falla en `file://`).

11. **Agregar campo al formulario OS**: HTML en `ordenes.html` → `getOrderFormData()` → body del fetch en `createOrder()` → `create-order.php` → `preparePdfData()` → funcion PDF.

12. **Arquitectura multi-pagina**: agregar pagina nueva = crear HTML + caso en `getCurrentPage()`, `navigateTo()` y `renderAll()`.

13. **Elemento no existe en pagina X**: todos los `els.xxx` pueden ser null. Nunca acceder sin null guard.

14. **`Clientes.html` en Linux**: desplegar como `clientes.html` (minusculas) en el servidor.

15. **Migraciones SQL**: usar `mcp_web_connector/scripts/run_migration.py`. El archivo va en `database/migrations/`.

16. **Pruebas SQL sin modificar datos**: usar `mcp_web_connector/scripts/test_consecutivo.py` como plantilla (hace ROLLBACK al final).

17. **Estado actual de la BD** (2026-05-30):
    - Tabla `orden_servicio`: 4 registros, max `numero_os=000703`, proxima = `000704`
    - Tabla `secuencias`: `nombre='orden_servicio'`, `valor=703`
    - Columnas `deleted_at` y `deleted_by` presentes en `orden_servicio`
