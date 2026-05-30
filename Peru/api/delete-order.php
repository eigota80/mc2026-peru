<?php
/**
 * POST /api/delete-order.php
 *
 * Eliminación LÓGICA de una orden de servicio.
 * NO hace DELETE físico. Marca deleted_at, deleted_by y estado='ELIMINADA'.
 * El numero_os queda reservado para siempre — no se reutiliza.
 *
 * Body JSON:
 *   {"id": 5, "deleted_by": "usr_xyz"}
 *
 * Respuesta OK:
 *   {"ok":true}
 * Respuesta error:
 *   {"ok":false,"error":"Descripción."}
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

function api_ok(): void {
    echo json_encode(['ok' => true], JSON_UNESCAPED_UNICODE);
    exit;
}

function api_fail(string $msg, int $code = 400): void {
    http_response_code($code);
    echo json_encode(['ok' => false, 'error' => $msg], JSON_UNESCAPED_UNICODE);
    exit;
}

/* ── Leer body ───────────────────────────────────────────────────────────── */

$body = json_decode(file_get_contents('php://input') ?: '{}', true);
if (!is_array($body)) {
    api_fail('Body JSON inválido.');
}

$id         = isset($body['id']) ? (int) $body['id'] : 0;
$deleted_by = trim($body['deleted_by'] ?? $body['created_by'] ?? 'os-system');

if ($id <= 0) {
    api_fail('id requerido y debe ser entero positivo.');
}

/* ── Soft-delete ─────────────────────────────────────────────────────────── */

$pdo = db();

try {
    /* Verificar que la orden existe y no está ya eliminada */
    $chk = $pdo->prepare(
        "SELECT id, numero_os, deleted_at FROM orden_servicio WHERE id = ? LIMIT 1"
    );
    $chk->execute([$id]);
    $row = $chk->fetch();

    if (!$row) {
        api_fail('Orden no encontrada.', 404);
    }

    if ($row['deleted_at'] !== null) {
        api_fail('La orden ya fue eliminada.', 409);
    }

    /* Marcar como eliminada — NO DELETE físico */
    $upd = $pdo->prepare(
        "UPDATE orden_servicio
         SET estado      = 'ELIMINADA',
             deleted_at  = NOW(),
             deleted_by  = ?
         WHERE id = ?"
    );
    $upd->execute([$deleted_by, $id]);

} catch (\PDOException $e) {
    error_log('[delete-order] PDOException: ' . $e->getMessage());
    api_fail('No se pudo eliminar la orden. Intente nuevamente.', 500);
}

api_ok();
