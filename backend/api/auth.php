<?php
require_once 'config.php';

$method = $_SERVER['REQUEST_METHOD'];
$action = $_GET['action'] ?? '';

if ($action === 'register' && $method === 'POST') {
    $body = getBody();
    $nombre   = trim($body['nombre'] ?? '');
    $correo   = strtolower(trim($body['correo'] ?? ''));
    $password = $body['contrasena'] ?? '';
    $sexo     = $body['sexo'] ?? null;
    $fecha    = $body['fecha_nac'] ?? null;

    if (!$nombre || !$correo || !$password)
        jsonResponse(['error' => 'Nombre, correo y contraseña son obligatorios.'], 400);
    if (strlen($password) < 8)
        jsonResponse(['error' => 'La contraseña debe tener al menos 8 caracteres.'], 400);
    if (!filter_var($correo, FILTER_VALIDATE_EMAIL))
        jsonResponse(['error' => 'El correo electrónico no es válido.'], 400);

    $db = getDB();
    $stmt = $db->prepare('SELECT id FROM usuarios WHERE correo = ?');
    $stmt->bind_param('s', $correo);
    $stmt->execute();
    if ($stmt->get_result()->num_rows > 0)
        jsonResponse(['error' => 'Ya existe una cuenta con ese correo.'], 409);

    $hashed = password_hash($password, PASSWORD_BCRYPT);
    $stmt = $db->prepare('INSERT INTO usuarios (nombre, correo, contrasena, sexo, fecha_nac, aviso_aceptado) VALUES (?, ?, ?, ?, ?, 1)');
    $stmt->bind_param('sssss', $nombre, $correo, $hashed, $sexo, $fecha);
    $stmt->execute();
    $nuevo_id = $db->insert_id;
    $token = generateToken($nuevo_id);
    jsonResponse(['token' => $token, 'nombre' => $nombre], 201);
}

if ($action === 'login' && $method === 'POST') {
    $body = getBody();
    $correo   = strtolower(trim($body['correo'] ?? ''));
    $password = $body['contrasena'] ?? '';

    if (!$correo || !$password)
        jsonResponse(['error' => 'Correo y contraseña son obligatorios.'], 400);

    $db = getDB();
    $stmt = $db->prepare('SELECT id, nombre, contrasena FROM usuarios WHERE correo = ?');
    $stmt->bind_param('s', $correo);
    $stmt->execute();
    $usuario = $stmt->get_result()->fetch_assoc();

    if (!$usuario)
        jsonResponse(['error' => 'No existe una cuenta con ese correo.'], 401);
    if (!password_verify($password, $usuario['contrasena']))
        jsonResponse(['error' => 'Contraseña incorrecta.'], 401);

    $token = generateToken($usuario['id']);
    jsonResponse(['token' => $token, 'nombre' => $usuario['nombre']]);
}

jsonResponse(['error' => 'Ruta no encontrada'], 404);
