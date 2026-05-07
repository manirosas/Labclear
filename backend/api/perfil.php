<?php
require_once 'config.php';

$method = $_SERVER['REQUEST_METHOD'];
$usuario_id = verifyToken();

if ($method === 'GET') {
    $db = getDB();
    $stmt = $db->prepare('SELECT nombre, correo, sexo, fecha_nac FROM usuarios WHERE id = ?');
    $stmt->bind_param('i', $usuario_id);
    $stmt->execute();
    $usuario = $stmt->get_result()->fetch_assoc();
    if (!$usuario) jsonResponse(['error' => 'Usuario no encontrado.'], 404);
    $usuario['fecha_nac'] = $usuario['fecha_nac'] ? (string)$usuario['fecha_nac'] : null;
    jsonResponse(['usuario' => $usuario]);
}

if ($method === 'PUT') {
    $body = getBody();
    $nombre    = trim($body['nombre'] ?? '');
    $correo    = strtolower(trim($body['correo'] ?? ''));
    $sexo      = $body['sexo'] ?? null;
    $fecha_nac = $body['fecha_nac'] ?? null;

    if (!$nombre || !$correo) jsonResponse(['error' => 'El nombre y correo son obligatorios.'], 400);
    if (!filter_var($correo, FILTER_VALIDATE_EMAIL)) jsonResponse(['error' => 'El correo no es válido.'], 400);

    $db = getDB();
    $stmt = $db->prepare('SELECT id FROM usuarios WHERE correo = ? AND id != ?');
    $stmt->bind_param('si', $correo, $usuario_id);
    $stmt->execute();
    if ($stmt->get_result()->num_rows > 0) jsonResponse(['error' => 'Ese correo ya está en uso.'], 409);

    $stmt = $db->prepare('UPDATE usuarios SET nombre = ?, correo = ?, sexo = ?, fecha_nac = ? WHERE id = ?');
    $stmt->bind_param('ssssi', $nombre, $correo, $sexo, $fecha_nac, $usuario_id);
    $stmt->execute();
    jsonResponse(['ok' => true, 'nombre' => $nombre]);
}

jsonResponse(['error' => 'Método no permitido'], 405);
