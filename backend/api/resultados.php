<?php
require_once 'config.php';

$method = $_SERVER['REQUEST_METHOD'];
$usuario_id = verifyToken();
$resultado_id = $_GET['id'] ?? null;

if ($method === 'GET' && !$resultado_id) {
    $db = getDB();
    $stmt = $db->prepare('SELECT id, tipo_estudio, fecha_estudio, valores, resumen_ia, estado, creado_en FROM resultados WHERE usuario_id = ? ORDER BY fecha_estudio DESC, creado_en DESC');
    $stmt->bind_param('i', $usuario_id);
    $stmt->execute();
    $rows = $stmt->get_result()->fetch_all(MYSQLI_ASSOC);
    foreach ($rows as &$r) {
        $r['valores'] = json_decode($r['valores'], true);
        $r['fecha_estudio'] = (string)$r['fecha_estudio'];
        $r['creado_en'] = (string)$r['creado_en'];
    }
    jsonResponse(['resultados' => $rows]);
}

if ($method === 'GET' && $resultado_id) {
    $db = getDB();
    $stmt = $db->prepare('SELECT id, tipo_estudio, fecha_estudio, valores, resumen_ia, estado FROM resultados WHERE id = ? AND usuario_id = ?');
    $stmt->bind_param('ii', $resultado_id, $usuario_id);
    $stmt->execute();
    $r = $stmt->get_result()->fetch_assoc();
    if (!$r) jsonResponse(['error' => 'Análisis no encontrado.'], 404);
    $r['valores'] = json_decode($r['valores'], true);
    $r['fecha_estudio'] = (string)$r['fecha_estudio'];
    jsonResponse(['resultado' => $r]);
}

if ($method === 'DELETE' && $resultado_id) {
    $db = getDB();
    $stmt = $db->prepare('DELETE FROM resultados WHERE id = ? AND usuario_id = ?');
    $stmt->bind_param('ii', $resultado_id, $usuario_id);
    $stmt->execute();
    if ($db->affected_rows === 0) jsonResponse(['error' => 'Análisis no encontrado.'], 404);
    jsonResponse(['ok' => true]);
}

jsonResponse(['error' => 'Ruta no encontrada'], 404);
