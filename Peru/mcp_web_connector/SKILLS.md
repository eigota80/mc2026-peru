# MCP Web Connector — Catalogo de Skills

> **Archivo de referencia para agentes AI.**
> Todo agente que trabaje en este proyecto DEBE usar este MCP para acceder al servidor y la base de datos.
> Credenciales en `.env`. Acceso directo via SSH sin MCP no esta permitido en modo produccion.

---

## Conexion rapida

| Parametro | Valor |
|---|---|
| Servidor MCP | `server.py` en este directorio |
| Protocolo | stdio JSON-RPC 2.0 (MCP 2024-11-05) |
| SSH host | `179.43.82.54:22` |
| DB | `bdmcperu` en MariaDB `127.0.0.1:3306` via tunel SSH |
| Raices permitidas | `/var/www`, `/home`, `/opt` |
| Limite lectura | 50 000 bytes por archivo |

Config en Claude Code → Settings → MCP Servers → archivo `mcp-config.example.json`.

---

## Skills disponibles hoy

### 1. `config_summary`
Muestra la configuracion activa del servidor MCP (sin secretos).

```json
{ "name": "config_summary" }
```

**Retorna:** ssh_host, db_host, db_name, allowed_roots, max_read_bytes, flags de si hay password/key.

**Usar cuando:** verificar que el agente cargo bien el `.env` antes de cualquier operacion.

---

### 2. `ssh_health`
Verifica acceso SSH y retorna informacion basica del servidor remoto.

```json
{ "name": "ssh_health" }
```

**Retorna:** hostname, usuario activo, kernel, directorio actual, version de MySQL, version de PHP.

**Usar cuando:** diagnosticar conectividad antes de una tarea; confirmar que el servidor esta activo.

---

### 3. `remote_list`
Lista archivos de un directorio remoto via SFTP.

```json
{
  "name": "remote_list",
  "arguments": {
    "path": "/var/www/html/Ordenes de servicios",
    "max_entries": 100
  }
}
```

| Parametro | Tipo | Default | Descripcion |
|---|---|---|---|
| `path` | string | `/var/www` | Ruta remota (debe estar en allowed_roots) |
| `max_entries` | int | 100 | Maximo 500 |

**Retorna:** lista de `{ name, size, mode, mtime }`.

**Usar cuando:** verificar que un archivo fue desplegado, explorar estructura de directorios del servidor.

---

### 4. `remote_read_text`
Lee el contenido de un archivo de texto remoto.

```json
{
  "name": "remote_read_text",
  "arguments": {
    "path": "/var/www/html/Ordenes de servicios/ordenes-servicio.js",
    "max_bytes": 50000
  }
}
```

| Parametro | Tipo | Default | Descripcion |
|---|---|---|---|
| `path` | string | — | Ruta remota completa |
| `max_bytes` | int | 50000 | Limite de bytes leidos |

**Retorna:** `{ path, size, truncated, content }`.

**Usar cuando:** inspeccionar un archivo en produccion sin bajar SSH manualmente; comparar version local vs servidor.

---

### 5. `mysql_query_readonly`
Ejecuta una consulta SELECT/SHOW/DESCRIBE en MariaDB via tunel SSH.

```json
{
  "name": "mysql_query_readonly",
  "arguments": {
    "sql": "SELECT * FROM empresa LIMIT 10",
    "database": "bdmcperu",
    "max_rows": 100
  }
}
```

| Parametro | Tipo | Default | Descripcion |
|---|---|---|---|
| `sql` | string | — | Solo SELECT, SHOW, DESCRIBE, EXPLAIN |
| `database` | string | `bdmcperu` | BD destino |
| `max_rows` | int | 100 | Maximo 500 |

**Retorna:** `{ columns, rows, row_count, truncated }`.

**Bloquea:** INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE y mas.

**Usar cuando:** consultar datos de clientes, cotizaciones, o cualquier tabla del sistema sin riesgo de modificar datos.

---

### 6. `mysql_list_tables`
Lista todas las tablas de la base de datos.

```json
{
  "name": "mysql_list_tables",
  "arguments": { "database": "bdmcperu" }
}
```

**Retorna:** lista de nombres de tablas.

**Usar cuando:** explorar el esquema antes de escribir una consulta; verificar si existe una tabla nueva.

---

### 7. `mysql_describe_table`
Describe las columnas de una tabla: tipos, nullable, claves.

```json
{
  "name": "mysql_describe_table",
  "arguments": {
    "table": "empresa",
    "database": "bdmcperu"
  }
}
```

| Parametro | Tipo | Default | Descripcion |
|---|---|---|---|
| `table` | string | — | Nombre de tabla (solo `[A-Za-z0-9_$]`) |
| `database` | string | `bdmcperu` | BD destino |

**Retorna:** `{ Field, Type, Null, Key, Default, Extra }` por columna.

**Usar cuando:** entender el esquema antes de escribir un query; generar formularios alineados a la BD.

---

### 8. `wordpress_users`
Busca usuarios en `wp_users` por login, email o display_name.

```json
{
  "name": "wordpress_users",
  "arguments": {
    "search": "eider",
    "max_rows": 20
  }
}
```

| Parametro | Tipo | Default | Descripcion |
|---|---|---|---|
| `search` | string | `""` | Filtro LIKE; vacio = todos |
| `max_rows` | int | 50 | Maximo registros |
| `database` | string | `bdmcperu` | BD WordPress |

**Retorna:** `ID, user_login, user_email, user_registered, display_name`.

---

### 9. `wordpress_options`
Lee opciones de `wp_options` (preview de 300 chars por valor para evitar desbordes).

```json
{
  "name": "wordpress_options",
  "arguments": {
    "search": "siteurl",
    "max_rows": 10
  }
}
```

| Parametro | Tipo | Default | Descripcion |
|---|---|---|---|
| `search` | string | `""` | Filtro por `option_name` |
| `max_rows` | int | 50 | Maximo registros |

**Retorna:** `option_id, option_name, option_value_preview (300 chars), autoload`.

---

### 10. `find_client_columns`
Detecta columnas de cualquier tabla cuyo nombre sugiera datos de clientes, documentos o contactos.

```json
{
  "name": "find_client_columns",
  "arguments": { "database": "bdmcperu" }
}
```

Busca nombres que contengan: `client`, `cliente`, `customer`, `razon`, `ruc`, `dni`, `contact`, `telefono`, `email`, `correo`.

**Retorna:** `TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY`.

**Usar cuando:** mapear de donde sacar datos de clientes para importar al sistema; hacer reverse-engineering del esquema.

---

### 11. `export_result_json`
Igual que `mysql_query_readonly` pero retorna el resultado ya serializado como string JSON listo para copiar o guardar.

```json
{
  "name": "export_result_json",
  "arguments": {
    "sql": "SELECT numerocorrelativo, razon_social, estado FROM cotizacion LIMIT 50",
    "max_rows": 200
  }
}
```

**Usar cuando:** generar un snapshot de datos para incrustar en un HTML de importacion o para logs.

---

## Tablas conocidas en `bdmcperu`

| Tabla | Descripcion | Campos clave |
|---|---|---|
| `empresa` | Clientes / empresas | `id`, `razon_social`, `ruc_dni`, `representante_legal`, `telefono`, `domicilio`, `email`, `contacto_tecnico`, `contacto_administrativo` |
| `cotizacion` | Cotizaciones | `id`, `numerocorrelativo`, `razon_social`, `ruc_dni`, `fecha`, `moneda`, `tipo`, `estado`, `comercial`, `observacion` |
| `cotizacion_detalle` | Lineas de cada cotizacion | `id`, `cotizacion_id`, `ciudad`, `servicio`, `mrc`, `dias_entrega`, `dir_origen`, `dir_destino`, `detalle` |

> Las **Ordenes de Servicio** viven en `localStorage` del navegador, **no** en MariaDB. El consecutivo empieza en 000700.

---

## Skills planificadas (futuras)

Las siguientes skills NO existen aun en `server.py`. Se documentan aqui para guiar el desarrollo.

---

### F-01. `remote_write_text` *(escritura de archivos)*
Escribir o reemplazar un archivo de texto en el servidor remoto.

**Parametros propuestos:**
| Param | Tipo | Descripcion |
|---|---|---|
| `path` | string | Ruta remota destino (dentro de allowed_roots) |
| `content` | string | Contenido completo del archivo |
| `encoding` | string | Default `utf-8` |

**Guardianes a implementar:** verificar ruta en `allowed_roots`; hacer backup automatico del archivo anterior en `/tmp/mcp_backup_<timestamp>/`; rechazar paths fuera de `/var/www`.

**Prioridad:** Alta — elimina el ciclo `local edit → scp manual → verify`.

---

### F-02. `remote_exec` *(ejecucion de comandos)*
Ejecutar un comando de shell en el servidor remoto.

**Parametros propuestos:**
| Param | Tipo | Descripcion |
|---|---|---|
| `command` | string | Comando a ejecutar |
| `timeout` | int | Segundos, default 30 |

**Guardianes a implementar:** lista blanca de comandos permitidos (ej. `cp`, `ls`, `chmod`, `service apache2 reload`); bloquear `rm -rf`, pipes con `curl`, redirecciones a archivos criticos.

**Prioridad:** Alta — necesario para `cp Clientes.html clientes.html` post-deploy y recarga de Apache.

---

### F-03. `remote_deploy_files` *(despliegue batch)*
Subir multiples archivos locales a una ruta remota en una sola llamada.

**Parametros propuestos:**
| Param | Tipo | Descripcion |
|---|---|---|
| `files` | array de `{ local_path, remote_path }` | Mapa local→remoto |
| `backup` | bool | Hacer backup antes de sobreescribir |

**Prioridad:** Alta — reemplaza el loop de `scp` actual.

---

### F-04. `mysql_write` *(escritura en BD con control)*
Ejecutar INSERT / UPDATE / DELETE de forma controlada, con log de auditoria.

**Parametros propuestos:**
| Param | Tipo | Descripcion |
|---|---|---|
| `sql` | string | Solo INSERT, UPDATE, DELETE (no DDL) |
| `params` | array | Parametros preparados |
| `database` | string | BD destino |

**Guardianes a implementar:** bloquear DROP, ALTER, CREATE, TRUNCATE; requerir parametros preparados (no concatenacion); escribir en tabla `mcp_audit_log` antes de ejecutar.

**Prioridad:** Media — actualmente el sistema escribe en `localStorage`; necesario si se migra a BD.

---

### F-05. `mysql_export_csv` *(exportar a CSV)*
Ejecutar un SELECT y retornar resultado en formato CSV.

**Parametros propuestos:**
| Param | Tipo | Descripcion |
|---|---|---|
| `sql` | string | Consulta SELECT |
| `delimiter` | string | Default `,` |
| `max_rows` | int | Default 1000 |

**Prioridad:** Media — util para generar reportes desde el modulo Informes.

---

### F-06. `db_backup` *(backup de base de datos)*
Crear un `mysqldump` de la base de datos y guardarlo en el servidor.

**Parametros propuestos:**
| Param | Tipo | Descripcion |
|---|---|---|
| `database` | string | BD a respaldar |
| `dest_path` | string | Ruta remota destino del `.sql.gz` |
| `tables` | array | Opcional: solo estas tablas |

**Prioridad:** Media — importante antes de migraciones o resets masivos.

---

### F-07. `apache_reload` *(recargar Apache)*
Ejecutar `service apache2 reload` o `systemctl reload httpd` de forma segura.

**Sin parametros** (comando fijo, no parametrizable).

**Prioridad:** Baja — actualmente Apache recarga automatico al escribir archivos; necesario si se usan configs de vhost.

---

### F-08. `server_disk_usage` *(uso de disco)*
Retornar el uso de disco del servidor remoto.

**Sin parametros.**

**Retorna:** output de `df -h` y `du -sh /var/www/html`.

**Prioridad:** Baja — util para monitoreo preventivo.

---

### F-09. `sync_orders_to_db` *(sincronizar OS a MariaDB)*
Leer ordenes de servicio del `localStorage` exportado y escribirlas en una tabla `orden_servicio` de MariaDB.

**Parametros propuestos:**
| Param | Tipo | Descripcion |
|---|---|---|
| `orders_json` | string | JSON de ordenes (formato `mcperu_os_orders`) |

**Requiere:** implementar primero `F-04 mysql_write` y crear tabla `orden_servicio` en BD.

**Prioridad:** Alta a futuro — para centralizar los datos y salir de `localStorage`.

---

### F-10. `validate_html_deploy` *(verificar deploy)*
Despues de subir un archivo HTML, verificar que el servidor retorna HTTP 200 y que el contenido incluye una cadena de version esperada.

**Parametros propuestos:**
| Param | Tipo | Descripcion |
|---|---|---|
| `url` | string | URL publica del archivo desplegado |
| `expected_string` | string | Cadena que debe aparecer en el response (ej. version del CSS) |

**Prioridad:** Media — cierra el ciclo de validacion del deploy sin abrir el navegador.

---

## Convenciones de versionado

Cada vez que se modifique `server.py` o se agregue una skill, actualizar el campo `version` en el handler de `initialize`:

```python
"serverInfo": {"name": "mcperu-web", "version": "0.2.0"},
```

Y actualizar este archivo con la nueva skill documentada.

---

## Agregar una skill nueva — pasos

1. Definir la funcion en `server.py` con el decorador `@tool()`.
2. Escribir el docstring en ingles (aparece en `tools/list`).
3. Agregar la skill a este archivo en la seccion correspondiente (disponibles o planificadas).
4. Actualizar la version en `serverInfo`.
5. Reiniciar el MCP en Claude Code: Settings → MCP Servers → reload.
6. Probar con `config_summary` primero para verificar que el servidor arranco.

---

*Ultima actualizacion: 2026-05-19 — v0.1.0 (11 skills disponibles, 10 skills planificadas)*
