<?php
require_once 'config.php';

$method = $_SERVER['REQUEST_METHOD'];
$usuario_id = verifyToken();

$campos = ['diabetes','embarazo','hipertension','dislipidemia','anemia','enfermedad_renal'];

if ($method === 'GET') {
    $db = getDB();
    $stmt = $db->prepare('SELECT * FROM antecedentes_clinicos WHERE usuario_id = ?');
    $stmt->bind_param('i', $usuario_id);
    $stmt->execute();
    $row = $stmt->get_result()->fetch_assoc();
    if (!$row) jsonResponse(['antecedentes' => null, 'completado' => false]);
    unset($row['id'], $row['usuario_id'], $row['creado_en']);
    jsonResponse(['antecedentes' => $row, 'completado' => true]);
}

if ($method === 'POST') {
    $body = getBody();
    $db = getDB();

    $stmt = $db->prepare('SELECT id FROM antecedentes_clinicos WHERE usuario_id = ?');
    $stmt->bind_param('i', $usuario_id);
    $stmt->execute();
    $existe = $stmt->get_result()->fetch_assoc();

    $vals = array_map(fn($c) => (int)(bool)($body[$c] ?? 0), $campos);

    if ($existe) {
        $set = implode(' = ?, ', $campos) . ' = ?';
        $stmt = $db->prepare("UPDATE antecedentes_clinicos SET $set WHERE usuario_id = ?");
        $types = str_repeat('i', count($campos)) . 'i';
        $stmt->bind_param($types, ...[...$vals, $usuario_id]);
    } else {
        $cols = implode(', ', $campos);
        $phs  = implode(', ', array_fill(0, count($campos), '?'));
        $stmt = $db->prepare("INSERT INTO antecedentes_clinicos (usuario_id, $cols) VALUES (?, $phs)");
        $types = 'i' . str_repeat('i', count($campos));
        $stmt->bind_param($types, $usuario_id, ...$vals);
    }
    $stmt->execute();

    $stmt = $db->prepare('UPDATE usuarios SET cuestionario_completado = 1 WHERE id = ?');
    $stmt->bind_param('i', $usuario_id);
    $stmt->execute();

    jsonResponse(['ok' => true]);
}

jsonResponse(['error' => 'Método no permitido'], 405);
