<?php
require_once 'config.php';

$method = $_SERVER['REQUEST_METHOD'];
$usuario_id = verifyToken();

if ($method === 'POST') {
    $body = getBody();
    $tipo_estudio  = trim($body['tipo_estudio'] ?? '');
    $fecha_estudio = trim($body['fecha_estudio'] ?? '');
    $valores       = $body['valores'] ?? [];

    if (!$tipo_estudio) jsonResponse(['error' => 'Debes seleccionar un tipo de estudio.'], 400);
    if (!$fecha_estudio) jsonResponse(['error' => 'Debes indicar la fecha del análisis.'], 400);
    if (empty($valores)) jsonResponse(['error' => 'Ingresa al menos un valor para analizar.'], 400);

    $db = getDB();

    // Cargar antecedentes
    $stmt = $db->prepare('SELECT * FROM antecedentes_clinicos WHERE usuario_id = ?');
    $stmt->bind_param('i', $usuario_id);
    $stmt->execute();
    $antecedentes = $stmt->get_result()->fetch_assoc() ?? [];

    // Generar resumen y estado
    $resumen = generarResumen($db, $tipo_estudio, $valores, $antecedentes);
    $estado  = calcularEstado($db, $valores, $antecedentes);

    $valores_json = json_encode($valores, JSON_UNESCAPED_UNICODE);
    $stmt = $db->prepare('INSERT INTO resultados (usuario_id, tipo_estudio, fecha_estudio, valores, resumen_ia, estado) VALUES (?, ?, ?, ?, ?, ?)');
    $stmt->bind_param('isssss', $usuario_id, $tipo_estudio, $fecha_estudio, $valores_json, $resumen, $estado);
    $stmt->execute();
    $nuevo_id = $db->insert_id;

    jsonResponse([
        'ok' => true,
        'resultado' => [
            'id'            => $nuevo_id,
            'tipo_estudio'  => $tipo_estudio,
            'fecha_estudio' => $fecha_estudio,
            'valores'       => $valores,
            'resumen_ia'    => $resumen,
            'estado'        => $estado,
        ]
    ], 201);
}

jsonResponse(['error' => 'Método no permitido'], 405);

// ─── Funciones de análisis ────────────────────────────────────────────────────

function getCondiciones($antecedentes) {
    $campos = ['diabetes','embarazo','hipertension','dislipidemia','anemia','enfermedad_renal'];
    return array_filter($campos, fn($c) => !empty($antecedentes[$c]));
}

function buscarRango($db, $parametro_id, $condiciones) {
    foreach ($condiciones as $condicion) {
        $stmt = $db->prepare('SELECT min_val, max_val, texto_normal, texto_alto, texto_bajo FROM rangos_condicion WHERE parametro_id = ? AND condicion = ?');
        $stmt->bind_param('is', $parametro_id, $condicion);
        $stmt->execute();
        $rango = $stmt->get_result()->fetch_assoc();
        if ($rango) return $rango;
    }
    $stmt = $db->prepare('SELECT min_val, max_val, texto_normal, texto_alto, texto_bajo FROM rangos_base WHERE parametro_id = ?');
    $stmt->bind_param('i', $parametro_id);
    $stmt->execute();
    return $stmt->get_result()->fetch_assoc();
}

function interpretarValor($db, $clave, $valor, $condiciones) {
    $stmt = $db->prepare('SELECT id, nombre, unidad FROM parametros WHERE clave = ?');
    $stmt->bind_param('s', $clave);
    $stmt->execute();
    $param = $stmt->get_result()->fetch_assoc();
    if (!$param) return null;

    $rango = buscarRango($db, $param['id'], $condiciones);
    if (!$rango) return null;

    $min = (float)$rango['min_val'];
    $max = (float)$rango['max_val'];

    if ($valor < $min) {
        $estado = 'bajo';
        $texto  = $rango['texto_bajo'] ?? '';
    } elseif ($valor > $max) {
        $estado = 'alto';
        $texto  = $rango['texto_alto'] ?? '';
    } else {
        $estado = 'normal';
        $texto  = $rango['texto_normal'] ?? '';
    }

    return [
        'estado'      => $estado,
        'explicacion' => $texto,
        'min'         => $min,
        'max'         => $max,
        'nombre'      => $param['nombre'],
        'unidad'      => $param['unidad'],
    ];
}

function calcularEstado($db, $valores, $antecedentes) {
    $condiciones = getCondiciones($antecedentes);
    $fuera = 0;
    foreach ($valores as $clave => $valor) {
        $r = interpretarValor($db, $clave, $valor, $condiciones);
        if ($r && $r['estado'] !== 'normal') $fuera++;
    }
    if ($fuera === 0) return 'normal';
    if ($fuera <= 2)  return 'precaucion';
    return 'alerta';
}

function generarResumen($db, $tipo_estudio, $valores, $antecedentes) {
    $condiciones = getCondiciones($antecedentes);
    $nombres_estudio = [
        'quimica'   => 'Química Sanguínea',
        'biometria' => 'Biometría Hemática',
        'lipidico'  => 'Perfil Lipídico',
        'renal'     => 'Función Renal',
        'hepatica'  => 'Función Hepática',
    ];
    $nombre_estudio = $nombres_estudio[$tipo_estudio] ?? $tipo_estudio;
    $etiquetas = [
        'diabetes' => 'Diabetes', 'embarazo' => 'Embarazo',
        'hipertension' => 'Hipertensión', 'dislipidemia' => 'Colesterol alto',
        'anemia' => 'Anemia', 'enfermedad_renal' => 'Enfermedad renal',
    ];

    $fuera_de_rango = [];
    $normales = [];

    foreach ($valores as $clave => $valor) {
        $r = interpretarValor($db, $clave, $valor, $condiciones);
        if (!$r) continue;
        if ($r['estado'] !== 'normal') {
            $fuera_de_rango[] = array_merge($r, ['valor' => $valor]);
        } else {
            $normales[] = $r['nombre'];
        }
    }

    $lineas = ["Interpretación de tu $nombre_estudio\n"];

    if (!empty($condiciones)) {
        $etqs = array_map(fn($c) => $etiquetas[$c] ?? $c, $condiciones);
        $lineas[] = "Esta interpretación fue personalizada considerando: " . implode(', ', $etqs) . ".\n";
    }

    if (!empty($fuera_de_rango)) {
        $lineas[] = "Valores que requieren atención:\n";
        foreach ($fuera_de_rango as $item) {
            $d = $item['estado'] === 'alto' ? 'ALTO' : 'BAJO';
            $lineas[] = "- {$item['nombre']}: {$item['valor']} {$item['unidad']} ($d)";
            if ($item['explicacion']) $lineas[] = "  {$item['explicacion']}\n";
        }
    } else {
        $lineas[] = "Todos tus valores se encuentran dentro del rango normal para tu perfil.\n";
    }

    if (!empty($normales)) {
        $lineas[] = "Valores en rango normal: " . implode(', ', $normales) . ".\n";
    }

    $n = count($fuera_de_rango);
    $t = count($valores);
    if ($n === 0) {
        $lineas[] = "Resumen: Tu análisis muestra resultados dentro de los parámetros normales. Continúa con tus hábitos y revisiones periódicas.";
    } elseif ($n <= 2) {
        $lineas[] = "Resumen: De $t parámetros evaluados, $n se encuentra(n) fuera del rango. Te recomendamos comentarlo con tu médico.";
    } else {
        $lineas[] = "Resumen: Se encontraron $n valores fuera del rango normal. Es recomendable que acudas con tu médico para una evaluación completa.";
    }

    $lineas[] = "\nAviso: Esta información es únicamente orientativa y educativa. No reemplaza el diagnóstico de un profesional de la salud. Ante cualquier duda, consulta a tu médico.";

    return implode("\n", $lineas);
}
