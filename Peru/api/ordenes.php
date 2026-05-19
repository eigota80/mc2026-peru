<?php
require __DIR__ . '/config.php';

$method = $_SERVER['REQUEST_METHOD'];
$pdo    = db();

/* ── GET ─────────────────────────────────────────────────────────────── */
if ($method === 'GET') {
    $stmt = $pdo->query(
        'SELECT id, numero_os, razon_social, ruc_dni, fecha, moneda, duracion,
                tipo_servicio, ciudad, dias_entrega, direccion_origen, direccion_destino,
                detalle, servicio, mrc, costo_instalacion, nrc, observacion,
                facilidades_pago, estado, created_by, created_at
         FROM orden_servicio
         ORDER BY id DESC
         LIMIT 1500'
    );
    $rows = $stmt->fetchAll();

    $data = array_map(function (array $r): array {
        $oid = (int) $r['id'];
        return [
            'id'                => 'ord_db_' . $oid,
            'db_id'             => $oid,
            'numero_os'         => $r['numero_os']          ?? '',
            'cliente_id'        => null,                        /* resuelto en JS por ruc_dni */
            'razon_social'      => $r['razon_social']        ?? '',
            'ruc_dni'           => $r['ruc_dni']             ?? '',
            'fecha'             => $r['fecha']               ?? '',
            'moneda'            => $r['moneda']              ?? 'SOLES',
            'duracion'          => $r['duracion']            ?? '',
            'tipo_servicio'     => $r['tipo_servicio']       ?? '',
            'ciudad'            => $r['ciudad']              ?? '',
            'dias_entrega'      => $r['dias_entrega']        ?? 0,
            'direccion_origen'  => $r['direccion_origen']    ?? '',
            'direccion_destino' => $r['direccion_destino']   ?? '',
            'detalle'           => $r['detalle']             ?? '',
            'servicio'          => $r['servicio']            ?? '',
            'mrc'               => (float) ($r['mrc']        ?? 0),
            'costo_instalacion' => $r['costo_instalacion']   ?? 'no',
            'nrc'               => (float) ($r['nrc']        ?? 0),
            'observacion'       => $r['observacion']         ?? '',
            'facilidades_pago'  => $r['facilidades_pago']   ?? '',
            'estado'            => $r['estado']              ?? 'Creada',
            'created_by'        => $r['created_by']          ?? '',
            'created_at'        => $r['created_at']          ?? null,
        ];
    }, $rows);

    ok($data, count($data));
}

/* ── POST: crear o actualizar ────────────────────────────────────────── */
if ($method === 'POST') {
    $body   = request_body();
    $action = $body['action'] ?? 'create';

    if ($action === 'update_status' && !empty($body['db_id'])) {
        $stmt = $pdo->prepare('UPDATE orden_servicio SET estado=? WHERE id=?');
        $stmt->execute([s($body['estado'] ?? 'Creada'), (int) $body['db_id']]);
        ok(['db_id' => (int) $body['db_id']]);
    }

    $num      = s($body['numero_os']         ?? '');
    $rsocial  = s($body['razon_social']      ?? '');
    $ruc      = s($body['ruc_dni']           ?? '');
    $fecha    = s($body['fecha']             ?? date('Y-m-d'));
    $moneda   = s($body['moneda']            ?? 'SOLES');
    $duracion = s($body['duracion']          ?? '');
    $tipo     = s($body['tipo_servicio']     ?? '');
    $ciudad   = s($body['ciudad']            ?? '');
    $dias     = (int)   ($body['dias_entrega']    ?? 0);
    $dOrigen  = s($body['direccion_origen']  ?? '');
    $dDestino = s($body['direccion_destino'] ?? '');
    $detalle  = s($body['detalle']           ?? '');
    $servicio = s($body['servicio']          ?? '');
    $mrc      = (float) ($body['mrc']        ?? 0);
    $costoInst = s($body['costo_instalacion'] ?? 'no');
    $nrc      = (float) ($body['nrc']        ?? 0);
    $obs      = s($body['observacion']       ?? '');
    $facil    = s($body['facilidades_pago']  ?? '');
    $estado   = s($body['estado']            ?? 'Creada');
    $user     = s($body['created_by']        ?? 'os-system');

    if ($num === '') {
        fail('numero_os requerido');
    }

    /* evitar duplicados por numero_os */
    $chk = $pdo->prepare('SELECT id FROM orden_servicio WHERE numero_os = ? LIMIT 1');
    $chk->execute([$num]);
    if ($chk->fetch()) {
        ok(['message' => 'ya existe', 'numero_os' => $num]);
    }

    $stmt = $pdo->prepare(
        'INSERT INTO orden_servicio
         (numero_os, razon_social, ruc_dni, fecha, moneda, duracion, tipo_servicio,
          ciudad, dias_entrega, direccion_origen, direccion_destino, detalle, servicio,
          mrc, costo_instalacion, nrc, observacion, facilidades_pago, estado, created_by)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    );
    $stmt->execute([
        $num, $rsocial, $ruc, $fecha, $moneda, $duracion, $tipo,
        $ciudad, $dias, $dOrigen, $dDestino, $detalle, $servicio,
        $mrc, $costoInst, $nrc, $obs, $facil, $estado, $user
    ]);
    $newId = (int) $pdo->lastInsertId();
    ok(['db_id' => $newId, 'id' => 'ord_db_' . $newId]);
}

fail('Metodo no soportado', 405);
