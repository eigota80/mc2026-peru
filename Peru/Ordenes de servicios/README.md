# Sistema de Ordenes de Servicio — Media Commerce Peru

Modulo comercial completo. Frontend puro: HTML + CSS + JS. Sin backend, sin librerias externas. Datos en `localStorage` del navegador.

---

## Indice

1. [Estructura de archivos](#estructura-de-archivos)
2. [Flujo de autenticacion](#flujo-de-autenticacion)
3. [Modulos del sistema](#modulos-del-sistema)
4. [Usuarios del sistema](#usuarios-del-sistema)
5. [localStorage — claves](#localstorage--claves)
6. [Modulo Cotizaciones](#modulo-cotizaciones)
7. [PDF — generacion nativa](#pdf--generacion-nativa)
8. [Reset de datos](#reset-de-datos)
9. [Importacion desde MariaDB](#importacion-desde-mariadb)
10. [Deploy al servidor](#deploy-al-servidor)
11. [Versionado de cache](#versionado-de-cache)
12. [Guia para AI futura](#guia-para-ai-futura)

---

## Estructura de archivos

```
Ordenes de servicios/
├── ordenes-servicio.html      # Login (pagina de entrada publica)
├── login.js                   # Logica de autenticacion
├── index.html                 # App completa (requiere sesion activa)
├── ordenes-servicio.js        # Todo el JS del sistema (~170 KB)
├── ordenes-servicio.css       # Estilos del sistema
├── Logo MC siempre presente-02 (1) (2).png  # Logo embebido en PDF como base64
└── README.md                  # Este archivo
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
| Ordenes | Crear OS + PDF, gestionar estados | `create_orders` / `update_orders` |
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

| Nombre | Email | Rol | Clave inicial |
|---|---|---|---|
| Eider Gonzalez | eider.gonzalez@mcperu.pe | administrador | GonzalezEider2024+ |
| Carol Paredes | carol.paredes@mcperu.pe | administrador | ParedesCarol2024+ |
| Renato Mejia | renato.mejia@mcperu.pe | comercial | MejiaRenato2023+ |
| Jorge Hesse | jorge.hesse@mcperu.pe | comercial | hessejorge2024+ |
| Gianpierre Velasquez | gianpierre.velasquez@mcperu.pe | comercial | GianVelasquez2024+ |
| Andres Romero | andres.romero@mcperu.pe | comercial | RomeroAndres2024+ |
| Gene Quispe | gene.quispe@mcperu.pe | comercial | MCPERU123 |
| Milagros Ravenna | milagros.ravenna@mcperu.pe | comercial | RAVENNA2025+ |
| Natanael Vargas | natanael.vargas@mcperu.pe | comercial | VarNata2023+ |

Para agregar un usuario: insertar en `seedUsers` y cambiar `USER_SEED_VERSION` a un valor nuevo (p.ej. `...-v4`).

---

## localStorage — claves

| Clave | Contenido |
|---|---|
| `mcperu_os_session` | Sesion activa |
| `mcperu_os_users` | Usuarios del sistema |
| `mcperu_os_users_seed_version` | Version del seed de usuarios |
| `mcperu_os_clients` | Clientes |
| `mcperu_os_orders` | Ordenes de servicio |
| `mcperu_service_order_next_number` | Consecutivo OS (empieza en 000700) |
| `mcperu_service_order_draft` | Borrador formulario OS |
| `mcperu_os_cotizaciones` | Cotizaciones |
| `mcperu_os_cot_next_number` | Consecutivo COT (empieza en 000652) |
| `mcperu_os_audit` | Log de auditoria (max 300 entradas) |
| `mcperu_os_data_version` | Version del reset de datos |

### Rango de numeracion

- **Cotizaciones historicas (MariaDB)**: 000001 – 000651
- **Ordenes de servicio nuevas**: 000700 en adelante
- **Cotizaciones nuevas**: 000652 en adelante

---

## Modulo Cotizaciones

Agregado en la sesion 2026-05-19. Pestaña **Cotizaciones** en el nav.

### Que hace

- Crea cotizaciones con **multiples lineas de servicio** (tabla dinamica: agregar/quitar filas)
- Cada linea: ciudad, servicio, MRC, dias de entrega, dir. origen, dir. destino, detalle
- PDF automatico al crear ("Cotizacion de Servicio Nro XXXXXX")
- Tabla con filtros por estado y por comercial
- Estados: NUEVA → EN REVISION → APROBADA → CERRADA / ANULADA
- Historial de 647 cotizaciones de MariaDB cargable via pagina importadora

### Schema de cotizacion en localStorage

```json
{
  "id": "cot_abc123",
  "db_id": 232,
  "numerocorrelativo": "000001",
  "cliente_id": null,
  "fecha": "2023-12-21",
  "rsocial": "WISPTEC PERU E.I.R.L.",
  "ruc_dni": "20610289712",
  "representante_legal": "...",
  "domicilio": "...",
  "telefono": "...",
  "moneda": "SOLES",
  "duracion": "24 MESES",
  "tipo": "RENOVACION UPGRADE",
  "valor_instalacion": 0,
  "estado": "CERRADO",
  "observacion": "...",
  "comercial": "RENATO MEJIA SILVA",
  "detalles": [
    {
      "ciudad": "LIMA",
      "servicio": "INTERNET",
      "renta": 4237.28,
      "dias_entrega": 3,
      "direccion_origen": "...",
      "direccion_destino": "...",
      "detalle": "..."
    }
  ],
  "created_at": "2023-12-21T00:00:00Z",
  "created_by": "importacion_mariadb"
}
```

---

## PDF — generacion nativa

PDF generado en JavaScript puro, sin librerias. Motor: `buildPdf()` + `buildServiceOrderContent()` (OS) / `buildCotizacionContent()` (COT).

- Formato A4: 595.276 x 841.89 pt
- Logo embebido como base64 en la constante `LOGO_B64` (linea ~18 del JS)
- Fuentes: Helvetica (`F1` normal, `F2` bold)
- PDF de cotizacion: hasta 10 lineas de servicio en una pagina

Para regenerar el logo base64 (si cambia el archivo PNG):
```javascript
// En consola del navegador, con el PNG accesible:
const img = new Image(); img.src = 'Logo MC...png';
const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
c.getContext('2d').drawImage(img, 0, 0);
console.log(c.toDataURL('image/png'));
```

---

## Reset de datos

### Reset automatico (por version)

```javascript
const DATA_VERSION_KEY = 'mcperu_os_data_version';
const DATA_VERSION     = 'reset-20260518-v1';
```

Cuando `DATA_VERSION` no coincide con localStorage, `resetOrders()` borra todas las ordenes y reinicia el consecutivo a 000700. Clientes y usuarios no se borran.

### Reset manual (administrador)

Modulo Usuarios → "Datos del sistema" → boton **Reiniciar ordenes**.

### Reset de seed de usuarios

```javascript
const USER_SEED_VERSION = 'cotizaciones-mediacommerce-20260518-v3';
```

Al cambiar este valor, el seed re-procesa `seedUsers`: actualiza datos de usuarios existentes y agrega los nuevos.

---

## Importacion desde MariaDB

La base `bdmcperu` en `179.43.82.54` contiene el historial comercial completo.

### Tablas relevantes

| Tabla | Registros | Descripcion |
|---|---|---|
| `empresa` | 450 | Clientes (RUC, razon social, contactos) |
| `cotizacion` | 827 (648 con correlativo) | Cotizaciones historicas |
| `cotizacion_detalle` | 787 | Lineas de servicio por cotizacion |
| `cotizacion_estado` | 4 | CERRADO (1), ANULADO (2), NUEVO (3), PENDIENTE ANULACION (4) |
| `cotizacion_tipo` | 13 | ALTA, BAJA, RENOVACION, UPGRADE, etc. |
| `cotizacion_moneda` | 2 | SOLES (1), DOLARES (2) |
| `wp_users` | 12 | Usuarios WordPress |

### Paginas de importacion desplegadas

| URL en produccion | Funcion |
|---|---|
| `https://www.mcperu.pe/importar-clientes.html` | Importa 448 clientes a `mcperu_os_clients` |
| `https://www.mcperu.pe/Ordenes%20de%20servicios/importar-cotizaciones.html` | Importa 647 cotizaciones a `mcperu_os_cotizaciones` |

**Uso**: abrir en el mismo navegador donde se usa el sistema, hacer clic en "Importar ahora". Eliminar del servidor despues de usar.

```bash
# Eliminar paginas de importacion del servidor
sshpass -p "M3d14C0msvc" ssh -o PasswordAuthentication=yes root@179.43.82.54 \
  "rm -f /var/www/html/importar-clientes.html \
         '/var/www/html/Ordenes de servicios/importar-cotizaciones.html'"
```

### Credenciales de acceso — MariaDB

```
Servidor : 179.43.82.54
SSH user : root
SSH pass : M3d14C0msvc

DB host  : 127.0.0.1 (localhost en el servidor)
DB port  : 3306
DB name  : bdmcperu
DB user  : root
DB pass  : Gestecno**
```

Conexion directa desde Mac:

```bash
export SSHPASS="M3d14C0msvc"
sshpass -e ssh -o StrictHostKeyChecking=no \
  -o PreferredAuthentications=password \
  -o PubkeyAuthentication=no \
  root@179.43.82.54 \
  'mysql -u root -pGestecno** bdmcperu -e "SHOW TABLES;"'
```

La password de MariaDB tambien esta en `/root/backup_wp/wp-config.php` del servidor como backup.

---

## Deploy al servidor

Produccion: `https://www.mcperu.pe` → Apache en `/var/www/html/`

### Deploy rapido

```bash
# 1. Subir archivos
sshpass -p "M3d14C0msvc" rsync -avz \
  "Peru/Ordenes de servicios/ordenes-servicio.js" \
  "Peru/Ordenes de servicios/ordenes-servicio.css" \
  "Peru/Ordenes de servicios/index.html" \
  root@179.43.82.54:'/var/www/html/Ordenes de servicios/'

# 2. Corregir nombre de directorio (rsync elimina espacios)
sshpass -p "M3d14C0msvc" ssh -o PasswordAuthentication=yes root@179.43.82.54 \
  'cp -r "/var/www/html/Ordenes/." "/var/www/html/Ordenes de servicios/" && rm -rf "/var/www/html/Ordenes"'
```

### Problema conocido: rsync y espacios

rsync transfiere `Ordenes de servicios/` como `Ordenes/`. El paso 2 es obligatorio en cada deploy.

---

## Versionado de cache

```html
<script src="ordenes-servicio.js?v=20260518-cot-v1"></script>
<link rel="stylesheet" href="ordenes-servicio.css?v=20260518-home-v1">
```

Incrementar el sufijo en cada deploy que modifique JS o CSS. Patron sugerido: `YYYYMMDD-descripcion-vN`.

---

## Guia para AI futura

1. **Frontend puro.** No hay servidor de aplicacion. Todo en `localStorage` del navegador.
2. **localStorage es por navegador y por origen.** Datos en un navegador no se ven en otro. Para distribuir: usar las paginas de importacion.
3. **Agregar usuario**: insertar en `seedUsers` + cambiar `USER_SEED_VERSION`.
4. **Forzar reset de ordenes**: cambiar `DATA_VERSION`.
5. **Deploy**: rsync + corrección de directorio + actualizar `?v=` del script.
6. **Conectar a MariaDB**: usar credenciales de la seccion Importacion. La clave de DB es `Gestecno**`.
7. **Cotizaciones vs Ordenes**: son modulos separados con claves de localStorage y consecutivos distintos.
8. **El PDF** no usa canvas para el logo (falla en `file://`). El logo esta como base64 en `LOGO_B64`.
9. **Agregar campo al formulario**: HTML → `cotizacionFromForm()` o `getOrderFormData()` → `prepareCotPdfData()` o `preparePdfData()` → funcion PDF.
10. **Coordenadas PDF**: en puntos (pt). La funcion `y(top)` convierte coordenadas de arriba-abajo a sistema PDF (abajo-arriba).
11. **`buildCotizacionContent()`** soporta max 10 lineas de servicio en una pagina.
12. **MariaDB desde AI**: `sshpass -e ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no root@179.43.82.54 'mysql -u root -pGestecno** bdmcperu -e "..."'`
