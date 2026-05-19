<?php
require __DIR__ . '/config.php';

$method = $_SERVER['REQUEST_METHOD'];
$pdo    = db();

/* ── GET: listar o buscar ──────────────────────────────────────────── */
if ($method === 'GET') {
    $q = s($_GET['q'] ?? '');

    if ($q !== '') {
        $like = '%' . $q . '%';
        $stmt = $pdo->prepare(
            'SELECT id, rsocial, nroid, nombre, domicilio, tel1, contec, cadmin, fecha_created
             FROM empresa
             WHERE rsocial LIKE ? OR nroid LIKE ?
             ORDER BY rsocial
             LIMIT 300'
        );
        $stmt->execute([$like, $like]);
    } else {
        $stmt = $pdo->query(
            'SELECT id, rsocial, nroid, nombre, domicilio, tel1, contec, cadmin, fecha_created
             FROM empresa
             ORDER BY rsocial
             LIMIT 1500'
        );
    }

    $rows = $stmt->fetchAll();
    $data = array_map(function (array $r): array {
        return [
            'id'                      => 'cli_db_' . $r['id'],
            'db_id'                   => (int) $r['id'],
            'razon_social'            => $r['rsocial']  ?? '',
            'ruc_dni'                 => $r['nroid']    ?? '',
            'representante_legal'     => $r['nombre']   ?? '',
            'domicilio'               => $r['domicilio'] ?? '',
            'telefono'                => $r['tel1']     ?? '',
            'contacto_tecnico'        => $r['contec']   ?? '',
            'contacto_administrativo' => $r['cadmin']   ?? '',
            'email'                   => '',
            'created_at'              => $r['fecha_created'] ?? null,
        ];
    }, $rows);

    ok($data, count($data));
}

/* ── POST: crear o actualizar ────────────────────────────────────────── */
if ($method === 'POST') {
    $body   = request_body();
    $action = $body['action'] ?? 'create';

    $razon = s($body['razon_social'] ?? '');
    $ruc   = s($body['ruc_dni']      ?? '');
    $rep   = s($body['representante_legal']     ?? '');
    $dom   = s($body['domicilio']               ?? '');
    $tel   = s($body['telefono']                ?? '');
    $ctec  = s($body['contacto_tecnico']        ?? '');
    $cadm  = s($body['contacto_administrativo'] ?? '');

    if ($razon === '') {
        fail('razon_social requerida');
    }

    if ($action === 'update' && !empty($body['db_id'])) {
        $stmt = $pdo->prepare(
            'UPDATE empresa
             SET rsocial=?, nombre=?, domicilio=?, tel1=?, contec=?, cadmin=?
             WHERE id=?'
        );
        $stmt->execute([$razon, $rep, $dom, $tel, $ctec, $cadm, (int) $body['db_id']]);
        ok(['db_id' => (int) $body['db_id'], 'id' => 'cli_db_' . (int) $body['db_id']]);
    }

    /* create */
    $stmt = $pdo->prepare(
        'INSERT INTO empresa (rsocial, nroid, nombre, domicilio, tel1, contec, cadmin)
         VALUES (?, ?, ?, ?, ?, ?, ?)'
    );
    $stmt->execute([$razon, $ruc, $rep, $dom, $tel, $ctec, $cadm]);
    $newId = (int) $pdo->lastInsertId();
    ok(['db_id' => $newId, 'id' => 'cli_db_' . $newId]);
}

fail('Metodo no soportado', 405);
