<?php
/**
 * POST /api/create-order.php
 *
 * Crea una orden de servicio con consecutivo atómico generado en BD.
 * El campo numero_os que envíe el frontend es ignorado — siempre se
 * genera aquí para garantizar unicidad global.
 *
 * Respuesta OK:
 *   {"ok":true,"id":5,"numero_os":"000704"}
 * Respuesta error:
 *   {"ok":false,"error":"Descripción del problema."}
 */
declare(strict_types=1);

require __DIR__ . '/config.php';

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'Método no permitido.']);
    exit;
}

/* ── Helpers locales ─────────────────────────────────────────────────────── */

function api_ok(array $data): void {
    echo json_encode(array_merge(['ok' => true], $data),
                     JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function api_fail(string $msg, int $code = 400): void {
    http_response_code($code);
    echo json_encode(['ok' => false, 'error' => $msg], JSON_UNESCAPED_UNICODE);
    exit;
}

/* ── Leer body JSON ──────────────────────────────────────────────────────── */

$body = json_decode(file_get_contents('php://input') ?: '{}', true);
if (!is_array($body)) {
    api_fail('Body JSON inválido.');
}

/* ── Validar campos requeridos ───────────────────────────────────────────── */

$razon_social     = trim($body['razon_social']      ?? '');
$ruc_dni          = trim($body['ruc_dni']           ?? '');
$fecha            = trim($body['fecha']             ?? date('Y-m-d'));
$moneda           = trim($body['moneda']            ?? 'SOLES');
$duracion         = trim($body['duracion']          ?? '');
$tipo_servicio    = trim($body['tipo_servicio']     ?? '');
$ciudad           = trim($body['ciudad']            ?? '');
$dias_entrega     = (int)  ($body['dias_entrega']   ?? 0);
$direccion_origen = trim($body['direccion_origen']  ?? '');
$direccion_destino= trim($body['direccion_destino'] ?? '');
$detalle          = trim($body['detalle']           ?? '');
$servicio         = trim($body['servicio']          ?? '');
$mrc              = (float)($body['mrc']            ?? 0.0);
$costo_instalacion= trim($body['costo_instalacion'] ?? 'no');
$nrc              = (float)($body['nrc']            ?? 0.0);
$observacion      = trim($body['observacion']       ?? '');
$facilidades_pago = trim($body['facilidades_pago']  ?? '');
$estado           = trim($body['estado']            ?? 'Creada');
$created_by       = trim($body['created_by']        ?? 'os-system');

if ($razon_social === '') {
    api_fail('razon_social es requerido.');
}

/* ── Transacción atómica ─────────────────────────────────────────────────── */

$pdo = db();

try {
    $pdo->beginTransaction();

    /* 1. Generar consecutivo atómico desde tabla secuencias */
    $upd = $pdo->prepare(
        "UPDATE secuencias
         SET valor = LAST_INSERT_ID(valor + 1)
         WHERE nombre = 'orden_servicio'"
    );
    $upd->execute();

    if ($upd->rowCount() === 0) {
        $pdo->rollBack();
        api_fail('Tabla secuencias no inicializada. Ejecutar migración primero.', 500);
    }

    $nextInt = (int) $pdo->query('SELECT LAST_INSERT_ID()')->fetchColumn();
    $numero_os = str_pad((string) $nextInt, 6, '0', STR_PAD_LEFT);

    /* 2. Insertar orden */
    $ins = $pdo->prepare(
        'INSERT INTO orden_servicio
           (numero_os, razon_social, ruc_dni, fecha, moneda, duracion,
            tipo_servicio, ciudad, dias_entrega, direccion_origen,
            direccion_destino, detalle, servicio, mrc, costo_instalacion,
            nrc, observacion, facilidades_pago, estado, created_by)
         VALUES
           (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    );
    $ins->execute([
        $numero_os, $razon_social, $ruc_dni, $fecha, $moneda, $duracion,
        $tipo_servicio, $ciudad, $dias_entrega, $direccion_origen,
        $direccion_destino, $detalle, $servicio, $mrc, $costo_instalacion,
        $nrc, $observacion, $facilidades_pago, $estado, $created_by,
    ]);

    $newId = (int) $pdo->lastInsertId();
    $pdo->commit();

} catch (\PDOException $e) {
    $pdo->rollBack();
    /* No exponer detalles internos al cliente */
    error_log('[create-order] PDOException: ' . $e->getMessage());
    api_fail('No se pudo crear la orden. Intente nuevamente.', 500);
}

api_ok(['id' => $newId, 'numero_os' => $numero_os]);
