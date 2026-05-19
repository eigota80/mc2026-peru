# Sistema de Ordenes de Servicio — Media Commerce Peru

Sistema web para gestion de clientes y Ordenes de Servicio de Media Commerce Peru. Funciona 100% en el navegador sin servidor backend. Los datos se persisten en `localStorage`.

---

## Indice

1. [Como abrir el sistema](#como-abrir-el-sistema)
2. [Flujo de navegacion](#flujo-de-navegacion)
3. [Estructura de archivos](#estructura-de-archivos)
4. [Roles y usuarios](#roles-y-usuarios)
5. [Flujo funcional](#flujo-funcional)
6. [Reglas de negocio](#reglas-de-negocio)
7. [Control de acceso](#control-de-acceso)
8. [Generacion de PDF](#generacion-de-pdf)
9. [Reset y administracion de datos](#reset-y-administracion-de-datos)
10. [Almacenamiento local](#almacenamiento-local)
11. [Seguridad](#seguridad)
12. [Deploy al servidor](#deploy-al-servidor)
13. [Base de datos — integracion futura](#base-de-datos--integracion-futura)
14. [Instrucciones para futuras IA](#instrucciones-para-futuras-ia)

---

## Como abrir el sistema

**En produccion:**
```
https://www.mcperu.pe/Ordenes%20de%20servicios/ordenes-servicio.html
```

**En local (sin servidor):**
```
Peru/Ordenes de servicios/ordenes-servicio.html
```

Ingresar con email y clave. Al autenticar, el sistema redirige automaticamente a `index.html`.

---

## Flujo de navegacion

```
ordenes-servicio.html  →  (login exitoso)  →  index.html
        ↑                                           |
        └──────── (sin sesion / logout) ────────────┘
```

- `ordenes-servicio.html`: solo el formulario de login. Si ya hay sesion activa, redirige directo a `index.html`.
- `index.html`: app completa. Si no hay sesion, redirige a `ordenes-servicio.html`.
- Al cerrar sesion (logout), regresa a `ordenes-servicio.html`.

---

## Estructura de archivos

```
Peru/
├── css/
│   └── core.min.css              (estilos globales + Font Awesome embebido)
├── style.css                     (estilos globales del sitio)
├── images/
│   └── system/favicon/
│       └── favicon-32x32.png
└── Ordenes de servicios/         ← esta carpeta
    ├── ordenes-servicio.html     (login — punto de entrada)
    ├── login.js                  (autenticacion, seed de usuarios/clientes, redireccion)
    ├── index.html                (app completa: dashboard, clientes, ordenes, usuarios)
    ├── ordenes-servicio.js       (logica: sesion, clientes, ordenes, PDF, reset)
    ├── ordenes-servicio.css      (estilos del modulo)
    ├── Logo MC siempre presente-02 (1) (2).png  (logo referencia)
    └── README.md
```

`core.min.css`, `style.css` e `images/` vienen del padre `../` via rutas relativas. No se duplican en esta carpeta.

**Nota sobre el logo:** embebido como base64 en la constante `LOGO_B64` de `ordenes-servicio.js`. Esto evita errores de canvas tainted en `file://`. Ver seccion [Actualizar el logo del PDF](#actualizar-el-logo-del-pdf).

---

## Roles y usuarios

### Roles y permisos

| Rol | Permisos |
|---|---|
| Administrador | Todo: usuarios, auditoria, todas las ordenes, reset de datos, activar OS |
| Comercial | Buscar/crear clientes, crear OS, imprimir PDF, ver sus propias ordenes |
| Operaciones | Actualizar estados, validar instalaciones, ver sus propias ordenes |
| Facturacion | Revisar MRC/NRC, validar activaciones, ver sus propias ordenes |

### Usuarios iniciales

Cargados automaticamente por `login.js` al primer acceso:

| Email | Rol | Clave |
|---|---|---|
| `eider.gonzalez@mcperu.pe` | Administrador | `GonzalezEider2024+` |
| `renato.mejia@mcperu.pe` | Comercial | `MejiaRenato2023+` |
| `milagros.ravenna@mcperu.pe` | Comercial | `RAVENNA2025+` |
| `natanael.vargas@mcperu.pe` | Comercial | `VarNata2023+` |
| `jorge.hesse@mcperu.pe` | Comercial | `hessejorge2024+` |
| `gianpierre.velasquez@mcperu.pe` | Comercial | `GianVelasquez2024+` |
| `gene.quispe@mcperu.pe` | Comercial | `MCPERU123` |

Si cambia el seed de usuarios, incrementar `USER_SEED_VERSION` en `login.js` para forzar recarga.

---

## Flujo funcional

1. Abrir `ordenes-servicio.html` → ingresar email y clave.
2. Login exitoso → redirige a `index.html` (dashboard).
3. Dashboard muestra metricas y ordenes recientes del usuario.
4. **Modulo Clientes:** buscar por RUC/DNI o razon social. Si existe, reutilizar. Si no, crear.
5. Seleccionar cliente para la orden.
6. **Modulo Ordenes:** completar formulario y crear OS.
7. PDF se genera y descarga automaticamente al crear la OS.
8. Vista previa de PDF disponible antes de guardar.

---

## Reglas de negocio

### Clientes — no duplicar

1. Buscar por RUC/DNI.
2. Buscar por razon social.
3. Si existe, reutilizar el registro.
4. Si no existe, crear cliente nuevo.

El sistema detecta duplicados automaticamente y reutiliza.

### Costo de instalacion (NRC)

- `costo_instalacion = si`: campo NRC habilitado, valor impreso en PDF.
- `costo_instalacion = no`: campo NRC deshabilitado, no aparece en PDF.

### Consecutivo de ordenes

- Se guarda en `localStorage` con clave `mcperu_service_order_next_number`.
- Inicia en `000700`.
- Solo el Administrador puede editarlo desde la barra de herramientas del modulo Ordenes.
- El reset de ordenes tambien reinicia el consecutivo a `000700`.

---

## Control de acceso

### Tres capas de proteccion en `ordenes-servicio.js`

1. **Botones de navegacion:** `data-permission="manage_users"`. La funcion `applyPermissions()` los oculta para roles sin ese permiso.
2. **Navegacion programatica:** `setView()` rechaza acceso a `usuarios` y `auditoria` si no hay `manage_users`, incluso desde la consola del navegador.
3. **Renderizado:** `renderAll()` ejecuta `renderUsers()` y `renderAudit()` solo si el usuario tiene `manage_users`.

### Visibilidad de ordenes

`getVisibleOrders()` centraliza el filtro:

- Administrador (`manage_users`): devuelve todas las ordenes.
- Cualquier otro rol: devuelve solo las ordenes donde `created_by === currentUser.id`.

Usada por `renderOrders()`, `renderMetrics()` y el dashboard.

---

## Generacion de PDF

100% en JavaScript nativo, sin librerias externas.

- Formato: PDF 1.4, pagina A4 (595.276 x 841.89 pt).
- Fuentes: Helvetica y Helvetica-Bold embebidas (Type1).
- Logo: constante `LOGO_B64` (`data:image/png;base64,...`) cargada con `new Image()`. Sin `fetch()` — funciona en `file://` sin errores de canvas tainted.
- Si el logo falla, el PDF se genera con texto de reemplazo.
- Nombre del archivo: `OS {numero} {RAZON SOCIAL}.pdf`.

### Estructura del PDF

```
[ LOGO ]                    Orden de Servicio Nro XXXXXX
                            Fecha  YYYY-MM-DD
────────────────────────────────────────────────────────
           Informacion general del cliente
────────────────────────────────────────────────────────
Razon social | RUC/DNI | Representante | Telefono
Domicilio | Contacto Tecnico | Contacto Administrativo
Moneda | Tipo de servicio
────────────────────────────────────────────────────────
┌──────────────────────────────────────────────────────┐
│ Ciudad | Dir. Origen | Detalle | Dir. Destino | ...  │
│ (fila de datos del servicio)                         │
└──────────────────────────────────────────────────────┘
                     Cargo Mensual sin IGV: XXX
                     Valor de la Instalacion: XXX  (solo si NRC aplica)
────────────────────────────────────────────────────────
Importante: La facturacion...
                     Observacion :
(texto libre — max 8 lineas)
────────────────────────────────────────────────────────
Facilidades de pago de instalacion :
────────────────────────────────────────────────────────
Esta orden es parte integral del contrato...
────────────────────────────────────────────────────────
        Cliente                    Comercial
Rep. Legal: ___     Nombre: ___
Firma: ___          Firma: ___
Fecha Firma: ___    DNI: ___
DNI/RUC: ___
```

### Reglas del encabezado

- Solo el logo. Sin direccion ni telefono corporativo.
- Datos adicionales van en el campo **Observaciones**.

### Campos del formulario de orden

Fecha, Moneda, Duracion, Tipo de servicio, Ciudad, Dias de entrega, Direccion origen, Direccion destino, Detalle, Servicio, MRC, Costo de instalacion, NRC, Observacion, Facilidades de pago.

No hay campos de direccion ni telefono corporativo — son datos fijos de Media Commerce.

### Firmas — posicion corregida

`Representante Legal:` mide ~87pt. El valor va en `x=188` (no en `x=130`) para evitar superposicion. Los demas labels de firma son mas cortos y mantienen el valor en `x=130`.

### Actualizar el logo del PDF

```bash
python3 -c "
import base64
with open('Logo MC siempre presente-02 (1) (2).png', 'rb') as f:
    print('const LOGO_B64 = \\'data:image/png;base64,' + base64.b64encode(f.read()).decode() + '\\';')
"
```

Reemplazar la linea `const LOGO_B64 = ...` en `ordenes-servicio.js` con el resultado. Luego hacer deploy.

---

## Reset y administracion de datos

### Reset automatico por version

`ordenes-servicio.js` contiene dos constantes de control:

```javascript
const DATA_VERSION_KEY = 'mcperu_os_data_version';
const DATA_VERSION     = 'reset-20260518-v1';
```

Al cargar la app, si el valor guardado en `localStorage[DATA_VERSION_KEY]` no coincide con `DATA_VERSION`, la funcion `resetOrders()` se ejecuta automaticamente:

- Borra todas las ordenes (`mcperu_os_orders`).
- Reinicia el consecutivo a `000700`.
- Elimina el borrador de formulario activo.
- Guarda la nueva version para no repetir el reset.

**Para forzar un nuevo reset en el futuro:** incrementar `DATA_VERSION` en `ordenes-servicio.js` y hacer deploy. Todos los usuarios verán su localStorage limpio al abrir la app.

```javascript
// Ejemplo para proxima limpieza:
const DATA_VERSION = 'reset-20260601-v1';
```

### Reset manual desde el panel de Administrador

En `index.html → Modulo Usuarios → seccion "Datos del sistema"`:

- Boton **Reiniciar ordenes** (visible solo para Administrador).
- Muestra un `confirm()` con el numero de ordenes que se van a eliminar.
- Al confirmar: borra todas las ordenes, reinicia el consecutivo a `000700`, registra la accion en Auditoria.
- Los clientes y usuarios **no** se eliminan.

### Que NO borra el reset

| Dato | Se borra con reset |
|---|---|
| Ordenes | Si |
| Consecutivo | Si (vuelve a 000700) |
| Borrador de formulario | Si |
| Clientes | No |
| Usuarios | No |
| Auditoria | No |
| Sesion activa | No |

---

## Almacenamiento local

| Clave localStorage | Contenido |
|---|---|
| `mcperu_os_users` | Lista de usuarios |
| `mcperu_os_clients` | Lista de clientes |
| `mcperu_os_orders` | Lista de ordenes |
| `mcperu_os_audit` | Registro de auditoria (max 300 entradas) |
| `mcperu_os_session` | Sesion activa (`user_id`, `started_at`) |
| `mcperu_service_order_next_number` | Consecutivo actual de OS |
| `mcperu_service_order_draft` | Borrador del formulario activo |
| `mcperu_os_users_seed_version` | Version del seed de usuarios |
| `mcperu_os_data_version` | Version de datos para reset automatico |

---

## Seguridad

- Password hash con SHA-256 via Web Crypto API (fallback FNV-1a si no disponible).
- Roles y permisos granulares por accion.
- Sesion persistida en `localStorage` con `user_id`.
- Auditoria de acciones visible solo para el Administrador.
- XSS prevenido con `escapeHtml()` en todo el renderizado dinamico.
- Formularios deshabilitados si el rol no tiene permiso de escritura.
- Reset de datos protegido por permiso `manage_users` y confirmacion explícita.

---

## Deploy al servidor

### Servidor de produccion

| Parametro | Valor |
|---|---|
| Host | `179.43.82.54` |
| Web root | `/var/www/html/` |
| Servidor web | Apache (httpd) |
| OS | CentOS / RHEL |
| URL produccion | `https://www.mcperu.pe` |
| Ruta del modulo | `/var/www/html/Ordenes de servicios/` |

### Comandos de deploy

Las credenciales SSH estan en `Peru/mcp_web_connector/.env` (`MCP_WEB_SSH_PASSWORD`).

```bash
SSH_PASS="<ver .env>"
LOCAL="$HOME/Documents/web side/MC_2026/Peru"
REMOTE="root@179.43.82.54"

# 1. Deploy HTML raiz (nav actualizada)
sshpass -p "$SSH_PASS" rsync -avz --include="*.html" --exclude="*" \
  "$LOCAL/" "$REMOTE:/var/www/html/"

# 2. Deploy subcarpetas HTML
for dir in asesoramiento blog soluciones normatividad-y-regulaciones; do
  sshpass -p "$SSH_PASS" rsync -avz --include="*.html" --exclude="*" \
    "$LOCAL/$dir/" "$REMOTE:/var/www/html/$dir/"
done

# 3. Deploy modulo Ordenes (atencion: espacio en el nombre)
sshpass -p "$SSH_PASS" rsync -avz --exclude="*.md" \
  "$LOCAL/Ordenes de servicios/" "$REMOTE:/var/www/html/Ordenes/"

# rsync no respeta el espacio — mover manualmente en el servidor:
sshpass -p "$SSH_PASS" ssh "$REMOTE" \
  "cp -r /var/www/html/Ordenes/. '/var/www/html/Ordenes de servicios/' && rm -rf /var/www/html/Ordenes"

# 4. Deploy sitemap y robots
sshpass -p "$SSH_PASS" rsync -avz "$LOCAL/sitemap.xml" "$LOCAL/robots.txt" "$REMOTE:/var/www/html/"

# 5. Permisos y recarga Apache
sshpass -p "$SSH_PASS" ssh "$REMOTE" \
  "chown -R apache:apache '/var/www/html/Ordenes de servicios/' && systemctl reload httpd"
```

### Problema conocido: espacio en el nombre del directorio

`rsync` no transfiere correctamente directorios con espacios en el nombre cuando se usa con `--rsh`. El directorio `Ordenes de servicios/` siempre llega al servidor como `Ordenes/`. **Solucion:** copiar los archivos del directorio mal nombrado al correcto y borrar el temporal, como se muestra en el paso 3 de arriba.

### Verificacion post-deploy

```bash
# Verificar HTTP en produccion
curl -s -o /dev/null -w "%{http_code}" https://www.mcperu.pe/
curl -s -o /dev/null -w "%{http_code}" "https://www.mcperu.pe/Ordenes%20de%20servicios/ordenes-servicio.html"
curl -s -o /dev/null -w "%{http_code}" "https://www.mcperu.pe/Ordenes%20de%20servicios/index.html"
```

Todos deben devolver `200`.

---

## Base de datos — integracion futura

Motor: MariaDB — base: `bdmcperu` — servidor: `179.43.82.54`

Actualmente el sistema opera 100% en `localStorage`. La integracion con MariaDB persistira clientes y ordenes en la base del hosting.

Conexion disponible mediante MCP Web Connector. Ver: `../mcp_web_connector/README.md`

### Esquema de tablas requeridas

**`usuarios`**: `id`, `nombre`, `email`, `password_hash`, `rol_id`, `estado`, `created_at`

**`roles`**: `id`, `nombre`

**`clientes`**: `id`, `razon_social`, `ruc_dni`, `representante_legal`, `telefono`, `domicilio`, `contacto_tecnico`, `contacto_administrativo`, `email`, `created_at`

**`ordenes_servicio`**: `id`, `numero_os`, `cliente_id`, `fecha`, `moneda`, `duracion`, `tipo_servicio`, `mrc`, `costo_instalacion`, `nrc`, `observacion`, `created_by`, `created_at`

**`ordenes_detalle`**: `id`, `orden_id`, `ciudad`, `direccion_origen`, `direccion_destino`, `detalle`, `servicio`, `dias_entrega`, `renta`

---

## Instrucciones para futuras IA

1. **Leer este archivo completo antes de tocar cualquier codigo.**
2. El punto de entrada es `ordenes-servicio.html` (login). La app vive en `index.html`.
3. La logica de login esta en `login.js`. La logica de la app en `ordenes-servicio.js`.
4. Los archivos locales van en la raiz de esta carpeta. No crear subcarpetas `css/` ni `js/`.
5. Los assets compartidos estan en `../` — referenciarlos con rutas relativas `../`.
6. El logo del PDF esta en `LOGO_B64` (base64). No usar `fetch()` para imagenes — falla en `file://`.
7. No romper la generacion de PDF: es codigo nativo sin librerias.
8. No romper el flujo comercial ni las reglas de control de acceso por rol.
9. Usuarios y Auditoria son exclusivos del Administrador. Cada usuario ve solo sus propias ordenes.
10. El reset de ordenes se controla con `DATA_VERSION` en `ordenes-servicio.js`. Para forzar un reset futuro, incrementar esa constante y hacer deploy.
11. Al hacer deploy: rsync no respeta espacios en nombres de directorio. Ver seccion [Deploy al servidor](#deploy-al-servidor) para el workaround correcto.
12. Despues de cambiar `ordenes-servicio.js` o `index.html`, incrementar el query string `?v=` en el `<script src>` de `index.html` para forzar recarga del cache en el navegador.
