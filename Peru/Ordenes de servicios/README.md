# Sistema de Ordenes de Servicio

## Objetivo del proyecto

Sistema web para gestion de clientes y Ordenes de Servicio de Media Commerce Peru.

Permite:

- Login con usuarios y roles.
- Gestion de clientes (busqueda, creacion, reutilizacion).
- Crear Ordenes de Servicio con detalle de servicios.
- Generar PDF con formato empresarial sin dependencias externas.
- Control comercial y operativo por rol.

---

## Como abrir el sistema

Abrir directamente en el navegador (sin servidor):

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

- `ordenes-servicio.html`: solo muestra el formulario de login. Si ya hay sesion activa, redirige directo a `index.html`.
- `index.html`: app completa. Si no hay sesion, redirige a `ordenes-servicio.html`.
- Al cerrar sesion (logout), regresa a `ordenes-servicio.html`.

---

## Estructura de archivos

```
Peru/
├── css/
│   └── core.min.css          (estilos globales + Font Awesome embebido)
├── style.css                  (estilos globales del sitio)
├── images/
│   └── system/favicon/
│       └── favicon-32x32.png
└── Ordenes de servicios/      ← esta carpeta
    ├── ordenes-servicio.html  (pagina de login — punto de entrada)
    ├── login.js               (logica de autenticacion y redireccion)
    ├── index.html             (app completa: dashboard, clientes, ordenes)
    ├── ordenes-servicio.js    (logica del app: sesion, clientes, ordenes, PDF)
    ├── ordenes-servicio.css   (estilos del modulo)
    ├── Logo MC siempre presente-02 (1) (2).png  (logo referencia — ver nota)
    └── README.md
```

Los archivos `core.min.css`, `style.css` e `images/` se toman de la carpeta padre `../` mediante rutas relativas. No se copian a esta carpeta.

**Nota sobre el logo:** el logo PNG esta embebido como base64 directamente dentro de `ordenes-servicio.js` (constante `LOGO_B64`). Esto evita errores de canvas tainted cuando el sistema se abre desde disco (`file://`). Si se reemplaza el logo, hay que regenerar la constante `LOGO_B64` en el JS.

---

## Roles del sistema

| Rol | Permisos |
|---|---|
| Administrador | Todo: usuarios, auditoria, todas las ordenes, activar OS |
| Comercial | Buscar/crear clientes, crear OS, imprimir PDF, ver sus ordenes |
| Operaciones | Actualizar estados, validar instalaciones, ver sus ordenes |
| Facturacion | Revisar MRC/NRC, validar activaciones, ver sus ordenes |

---

## Usuarios iniciales

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

Si el seed cambia, actualizar `USER_SEED_VERSION` en `login.js` para forzar recarga.

---

## Flujo funcional

1. Abrir `ordenes-servicio.html` → ingresar email y clave.
2. Login exitoso → redirige a `index.html` (dashboard).
3. Dashboard muestra metricas y ordenes recientes del usuario.
4. Modulo Clientes: buscar por RUC/DNI o razon social antes de crear.
5. Seleccionar cliente existente o crear uno nuevo.
6. Modulo Ordenes: completar formulario y crear OS.
7. PDF se genera y descarga automaticamente al crear la OS.
8. Vista previa de PDF disponible antes de guardar.

---

## Reglas de negocio

### Clientes

Antes de crear un cliente:

1. Buscar por RUC/DNI.
2. Buscar por razon social.
3. Si existe, reutilizar el registro.
4. Si no existe, crear cliente nuevo.

Regla obligatoria: no duplicar clientes. El sistema detecta duplicados por RUC/DNI o razon social y reutiliza automaticamente.

### Costo de instalacion (NRC)

- Si `costo_instalacion` es `si`: el campo NRC se habilita y el PDF imprime el valor.
- Si `costo_instalacion` es `no`: el campo NRC se deshabilita y el PDF no muestra ningun valor de instalacion.

### Consecutivo de ordenes

El numero de la siguiente OS se guarda en `localStorage`. Inicia en `000700`. Solo el Administrador puede editarlo desde la barra de herramientas del modulo Ordenes.

---

## Control de acceso por rol

### Tres capas de proteccion en `ordenes-servicio.js`

1. **Botones de navegacion**: llevan `data-permission="manage_users"`. La funcion `applyPermissions()` los oculta y deshabilita para roles sin ese permiso.
2. **Navegacion programatica**: `setView()` rechaza el acceso a `usuarios` y `auditoria` si el usuario no tiene `manage_users`, incluso si se intenta desde la consola del navegador.
3. **Renderizado**: `renderAll()` solo ejecuta `renderUsers()` y `renderAudit()` cuando el usuario tiene `manage_users`, evitando que los datos queden en el DOM.

### Visibilidad de ordenes

La funcion `getVisibleOrders()` centraliza el filtro:

- Administrador (`manage_users`): devuelve todas las ordenes.
- Cualquier otro rol: devuelve solo las ordenes donde `created_by === currentUser.id`.

Usada por `renderOrders()`, `renderMetrics()` y el dashboard.

---

## Generacion de PDF

El PDF se genera 100% en JavaScript sin librerias externas (`ordenes-servicio.js`).

- Formato: PDF 1.4, pagina A4 (595 x 842 pt).
- Fuentes: Helvetica y Helvetica-Bold embebidas (Type1).
- Logo: embebido como base64 en la constante `LOGO_B64` dentro de `ordenes-servicio.js`. Se carga con `new Image()` directo desde el data URL, sin `fetch()`, lo que garantiza compatibilidad en `file://` sin errores de canvas tainted.
- Si el logo falla, el PDF se genera con texto de reemplazo.
- Nombre del archivo descargado: `OS {numero} {RAZON SOCIAL}.pdf`.

### Estructura del PDF (de arriba hacia abajo)

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
│ Ciudad | Dir. Origen | Detalle | Dir. Destino | ...  │  ← resumen del servicio
│ (fila de datos)                                      │
└──────────────────────────────────────────────────────┘
                     Cargo Mensual sin IGV: XXX
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

**Orden de secciones:** la tabla de servicios va inmediatamente despues de los datos del cliente. Las observaciones y facilidades de pago van debajo de la tabla, antes de las firmas.

### Reglas del encabezado

- El area del logo muestra **unicamente el logo**. No se imprime direccion ni telefono corporativo.
- Si se necesita incluir direccion o datos de contacto adicionales, se escriben en el campo **Observaciones** del formulario.

### Campos del formulario de orden

El formulario de orden contiene: Fecha, Moneda, Duracion, Tipo de servicio, Ciudad, Dias de entrega, Direccion origen, Direccion destino, Detalle, Servicio, MRC, Costo de instalacion, NRC, Observacion, Facilidades de pago.

**No existen campos de direccion ni telefono corporativo en el formulario** — esos datos son fijos de Media Commerce y no se ingresan por orden.

### Firmas — correccion de layout

El label `Representante Legal:` mide ~87pt. El valor del nombre se posiciona en x=188 (no en x=130) para evitar que el texto se monte sobre el label. Los demas labels de firma (`Firma:`, `Fecha de Firma:`, `DNI/RUC:`) son mas cortos y mantienen el valor en x=130.

### Actualizar el logo del PDF

Si se cambia la imagen del logo, regenerar `LOGO_B64` en `ordenes-servicio.js`:

```bash
python3 -c "
import base64
with open('Logo MC siempre presente-02 (1) (2).png', 'rb') as f:
    print('const LOGO_B64 = \\'data:image/png;base64,' + base64.b64encode(f.read()).decode() + '\\';')
"
```

Reemplazar la linea `const LOGO_B64 = ...` en `ordenes-servicio.js` con el resultado.

---

## Almacenamiento local (localStorage)

| Clave | Contenido |
|---|---|
| `mcperu_os_users` | Lista de usuarios |
| `mcperu_os_clients` | Lista de clientes |
| `mcperu_os_orders` | Lista de ordenes |
| `mcperu_os_audit` | Registro de auditoria (max 300 entradas) |
| `mcperu_os_session` | Sesion activa (`user_id`, `started_at`) |
| `mcperu_service_order_next_number` | Consecutivo actual de OS |
| `mcperu_service_order_draft` | Borrador del formulario activo |
| `mcperu_os_users_seed_version` | Version del seed de usuarios |

---

## Seguridad

- Password hash con SHA-256 via Web Crypto API (fallback FNV-1a si no disponible).
- Roles y permisos granulares por accion.
- Sesion persistida en `localStorage` con `user_id`.
- Auditoria de acciones visible solo para el Administrador.
- XSS prevenido con `escapeHtml()` en todo el renderizado dinamico.
- Formularios deshabilitados si el rol no tiene permiso de escritura.

---

## Base de datos (integracion futura)

Motor: MariaDB — base: `bdmcperu`

Conexion disponible mediante MCP Web Connector (solo lectura) via SSH al servidor `179.43.82.54`.

Ver: `../mcp_web_connector/README.md`

Actualmente el sistema opera 100% en `localStorage`. La integracion con MariaDB es un paso futuro para persistir clientes y ordenes en la base de datos del hosting.

### Esquema de tablas requeridas

**`usuarios`**: `id`, `nombre`, `email`, `password_hash`, `rol_id`, `estado`, `created_at`

**`roles`**: `id`, `nombre`

**`clientes`**: `id`, `razon_social`, `ruc_dni`, `representante_legal`, `telefono`, `domicilio`, `contacto_tecnico`, `contacto_administrativo`, `email`, `created_at`

**`ordenes_servicio`**: `id`, `numero_os`, `cliente_id`, `fecha`, `moneda`, `duracion`, `tipo_servicio`, `mrc`, `costo_instalacion`, `nrc`, `observacion`, `created_by`, `created_at`

**`ordenes_detalle`**: `id`, `orden_id`, `ciudad`, `direccion_origen`, `direccion_destino`, `detalle`, `servicio`, `dias_entrega`, `renta`

---

## Git

Repositorio: `MC2026` — Ramas: `main`, `develop`, `feature/*`

---

## Instrucciones para futuras IA

1. Leer este archivo completo antes de tocar cualquier codigo.
2. El punto de entrada es `ordenes-servicio.html` (login). El app vive en `index.html`.
3. La logica de login esta en `login.js`. La logica del app en `ordenes-servicio.js`.
4. Los archivos locales van en la raiz de esta carpeta — no crear subcarpetas `css/` ni `js/`.
5. Los assets compartidos (CSS global, imagenes, favicon) estan en `../` y se referencian con rutas relativas `../`.
6. El logo del PDF esta embebido como base64 en `ordenes-servicio.js` (constante `LOGO_B64`). No usar `fetch()` para cargar imagenes — falla en `file://`.
7. No romper la generacion de PDF: es codigo nativo sin librerias, tocar con cuidado.
8. No romper el flujo comercial ni las reglas de control de acceso.
9. Respetar: Usuarios y Auditoria son exclusivos del Administrador. Cada usuario solo ve sus propias ordenes.
