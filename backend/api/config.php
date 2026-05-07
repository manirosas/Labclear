<?php
define('DB_HOST', 'srv1137.hstgr.io');
define('DB_USER', 'u879881475_manirosas');
define('DB_PASS', 'Gomugomuno12@');
define('DB_NAME', 'u879881475_Labclear');
define('JWT_SECRET', 'k9#mP2$xQw8@nL5vRj3&hY7cZt4*bN6eAsDf0gUiOp1qWrEy');
define('JWT_EXPIRY', 8 * 3600); // 8 horas

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

function getDB() {
    $conn = new mysqli(DB_HOST, DB_USER, DB_PASS, DB_NAME);
    $conn->set_charset('utf8mb4');
    if ($conn->connect_error) {
        http_response_code(500);
        echo json_encode(['error' => 'Error de conexión a la base de datos']);
        exit();
    }
    return $conn;
}

function jsonResponse($data, $code = 200) {
    http_response_code($code);
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit();
}

function base64url_encode($data) {
    return rtrim(strtr(base64_encode($data), '+/', '-_'), '=');
}

function base64url_decode($data) {
    return base64_decode(strtr($data, '-_', '+/') . str_repeat('=', 3 - (3 + strlen($data)) % 4));
}

function generateToken($usuario_id) {
    $header = base64url_encode(json_encode(['alg' => 'HS256', 'typ' => 'JWT']));
    $payload = base64url_encode(json_encode([
        'usuario_id' => $usuario_id,
        'exp' => time() + JWT_EXPIRY
    ]));
    $signature = base64url_encode(hash_hmac('sha256', "$header.$payload", JWT_SECRET, true));
    return "$header.$payload.$signature";
}

function verifyToken() {
    $auth = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
    if (!str_starts_with($auth, 'Bearer ')) {
        jsonResponse(['error' => 'Token no proporcionado'], 401);
    }
    $token = substr($auth, 7);
    $parts = explode('.', $token);
    if (count($parts) !== 3) {
        jsonResponse(['error' => 'Token inválido'], 401);
    }
    [$header, $payload, $sig] = $parts;
    $expectedSig = base64url_encode(hash_hmac('sha256', "$header.$payload", JWT_SECRET, true));
    if (!hash_equals($expectedSig, $sig)) {
        jsonResponse(['error' => 'Token inválido'], 401);
    }
    $data = json_decode(base64url_decode($payload), true);
    if ($data['exp'] < time()) {
        jsonResponse(['error' => 'Token expirado'], 401);
    }
    return $data['usuario_id'];
}

function getBody() {
    return json_decode(file_get_contents('php://input'), true) ?? [];
}
