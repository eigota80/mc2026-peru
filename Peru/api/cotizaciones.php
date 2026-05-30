<?php
require __DIR__ . '/config.php';

/* Tablas de codigos de MariaDB */
const ESTADO_MAP = ['1' => 'CERRADO', '2' => 'ANULADO', '3' => 'NUEVA', '4' => 'PENDIENTE ANULACION', 'N' => 'NUEVA'];
const TIPO_MAP   = [
    '1'  => 'TRASLADO',    '2'  => 'SOLICITUD',   '3'  => 'ALTA',
    '4'  => 'BAJA',        '5'  => 'UPGRADE',      '6'  => 'RENOVACION',
    '7'  => 'RENOVACION UPGRADE', '8' => 'RENOVACION DOWNGRADE',
    '9'  => 'VENTA UNICA', '10' => 'MANTENIMIENTO','11' => 'DOWNGRADE',
    '12' => 'PRUEBAS',     '13' => 'SUSPENSION',
];
const MONEDA_MAP = ['1' => 'SOLES', '2' => 'USD'];

$method = $_SERVER['REQUEST_METHOD'];
$pdo    = db();

/* ── GET ─────────────────────────────────────────────────────────────── */
if ($method === 'GET') {
    $stmt = $pdo->query(
        'SELECT id, empresa_id, numerocorrelativo, rsocial, nroidentificacion,
                nombre, domicilio, tel1, moneda, duracion_os, tipo,
                valor_instalacion, estado, observacion, comercial,
                fecha, user_created, fecha_updated
         FROM cotizacion
         ORDER BY id DESC
         LIMIT 300'
    );
    $rows = $stmt->fetchAll();

    /* detalles en un solo query */
    $ids = array_column($rows, 'id');
    $detallesMap = [];
    if ($ids) {
        $ph   = implode(',', array_fill(0, count($ids), '?'));
        $dStmt = $pdo->prepare(
            "SELECT cotizacion_id, ciudad, servicio, renta, dias_entrega,
                    direccion_o, direccion_d, detalle
             FROM cotizacion_detalle
             WHERE cotizacion_id IN ($ph)
             ORDER BY id"
        );
        $dStmt->execute($ids);
        foreach ($dStmt->fetchAll() as $d) {
            $detallesMap[$d['cotizacion_id']][] = [
                'ciudad'            => $d['ciudad']      ?? '',
                'servicio'          => $d['servicio']    ?? '',
                'renta'             => (float) ($d['renta']         ?? 0),
                'dias_entrega'      => (int)   ($d['dias_entrega']  ?? 0),
                'direccion_origen'  => $d['direccion_o'] ?? '',
                'direccion_destino' => $d['direccion_d'] ?? '',
                'detalle'           => $d['detalle']     ?? '',
            ];
        }
    }

    $data = array_map(function (array $r) use ($detallesMap): array {
        $ec  = (string) ($r['estado'] ?? '');
        $tc  = (string) ($r['tipo']   ?? '');
        $mc  = (string) ($r['moneda'] ?? '');
        $cid = (int) $r['id'];

        /* fecha: preferir campo fecha, fallback a fecha_updated */
        $fecha = $r['fecha'] ?? ($r['fecha_updated'] ? substr($r['fecha_updated'], 0, 10) : '');

        return [
            'id'                => 'cot_db_' . $cid,
            'db_id'             => $cid,
            'numerocorrelativo' => $r['numerocorrelativo']  ?? '',
            'cliente_id'        => null,                        /* resuelto en JS por ruc_dni */
            'razon_social'      => $r['rsocial']             ?? '',
            'ruc_dni'           => $r['nroidentificacion']   ?? '',
            'representante_legal' => $r['nombre']             ?? '',
            'domicilio'         => $r['domicilio']           ?? '',
            'telefono'          => $r['tel1']                ?? '',
            'fecha'             => is_string($fecha) ? $fecha : '',
            'moneda'            => MONEDA_MAP[$mc] ?? 'SOLES',
            'duracion'          => $r['duracion_os']         ?? '',
            'tipo'              => TIPO_MAP[$tc]   ?? $tc,
            'valor_instalacion' => (float) ($r['valor_instalacion'] ?? 0),
            'estado'            => ESTADO_MAP[$ec] ?? 'NUEVA',
            'observacion'       => $r['observacion']         ?? '',
            'comercial'         => $r['comercial']           ?? '',
            'created_by'        => $r['user_created']        ?? '',
            'created_at'        => $r['fecha_updated']       ?? null,
            'detalles'          => $detallesMap[$cid]        ?? [],
        ];
    }, $rows);

    ok($data, count($data));
}

/* ── POST: crear cotizacion ──────────────────────────────────────────── */
if ($method === 'POST') {
    $body   = request_body();
    $action = $body['action'] ?? 'create';

    $num      = s($body['numerocorrelativo'] ?? '');
    $rsocial  = s($body['razon_social']      ?? '');
    $ruc      = s($body['ruc_dni']           ?? '');
    $nombre   = s($body['representante_legal'] ?? '');
    $dom      = s($body['domicilio']         ?? '');
    $tel      = s($body['telefono']          ?? '');
    $fecha    = s($body['fecha']             ?? date('Y-m-d'));
    $comercial = s($body['comercial']        ?? '');
    $observacion = s($body['observacion']    ?? '');
    $duracion = s($body['duracion']          ?? '');
    $nrc      = (float) ($body['valor_instalacion'] ?? 0);
    $user     = s($body['created_by']        ?? 'os-system');
    $detalles = is_array($body['detalles'] ?? null) ? $body['detalles'] : [];

    /* Resolver codigos inversos */
    $monedaCode = '1';
    foreach (MONEDA_MAP as $k => $v) {
        if (strtoupper(s($body['moneda'] ?? '')) === $v) { $monedaCode = $k; break; }
    }
    $tipoCode = '3';
    foreach (TIPO_MAP as $k => $v) {
        if (strtoupper(s($body['tipo'] ?? '')) === $v) { $tipoCode = $k; break; }
    }
    $estadoCode = '3';

    /* Si ya existe por numerocorrelativo, actualizar estado */
    if ($action === 'update' && !empty($body['db_id'])) {
        $ec = '3';
        foreach (ESTADO_MAP as $k => $v) {
            if (strtoupper(s($body['estado'] ?? '')) === $v) { $ec = $k; break; }
        }
        $stmt = $pdo->prepare('UPDATE cotizacion SET estado=? WHERE id=?');
        $stmt->execute([$ec, (int) $body['db_id']]);
        ok(['db_id' => (int) $body['db_id']]);
    }

    /* buscar empresa_id */
    $empId = null;
    if ($ruc !== '') {
        $es = $pdo->prepare('SELECT id FROM empresa WHERE nroid = ? LIMIT 1');
        $es->execute([$ruc]);
        $er = $es->fetch();
        if ($er) { $empId = (int) $er['id']; }
    }

    $stmt = $pdo->prepare(
        'INSERT INTO cotizacion
         (empresa_id, numerocorrelativo, rsocial, nroidentificacion, nombre, domicilio, tel1,
          fecha, moneda, duracion_os, tipo, valor_instalacion, estado, observacion, comercial, user_created)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    );
    $stmt->execute([
        $empId, $num, $rsocial, $ruc, $nombre, $dom, $tel,
        $fecha, $monedaCode, $duracion, $tipoCode, $nrc,
        $estadoCode, $observacion, $comercial, $user
    ]);
    $newId = (int) $pdo->lastInsertId();

    /* insertar detalles */
    if ($detalles && $newId) {
        $ds = $pdo->prepare(
            'INSERT INTO cotizacion_detalle
             (cotizacion_id, ciudad, servicio, renta, dias_entrega, direccion_o, direccion_d, detalle)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
        );
        foreach ($detalles as $d) {
            $ds->execute([
                $newId,
                s($d['ciudad']            ?? ''),
                s($d['servicio']          ?? ''),
                (float) ($d['renta']      ?? 0),
                (int)   ($d['dias_entrega'] ?? 0),
                s($d['direccion_origen']  ?? ''),
                s($d['direccion_destino'] ?? ''),
                s($d['detalle']           ?? ''),
            ]);
        }
    }

    ok(['db_id' => $newId, 'id' => 'cot_db_' . $newId]);
}

fail('Metodo no soportado', 405);
