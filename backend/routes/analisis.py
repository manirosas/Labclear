from flask import Blueprint, request, jsonify
from db import get_connection
from auth_helpers import login_requerido
from motor_analisis import generar_resumen, calcular_estado, _condiciones_activas
import json

analisis_bp = Blueprint('analisis', __name__)


def _cargar_antecedentes(cursor, usuario_id):
    cursor.execute(
        '''SELECT diabetes, embarazo, hipertension, dislipidemia, anemia, enfermedad_renal
           FROM antecedentes_clinicos WHERE usuario_id = %s''',
        (usuario_id,)
    )
    row = cursor.fetchone()
    if not row:
        return {}
    return {k: bool(v) for k, v in row.items()}


@analisis_bp.route('/analizar', methods=['POST'])
@login_requerido
def analizar(usuario_id):
    data = request.get_json()

    tipo_estudio  = data.get('tipo_estudio', '').strip()
    fecha_estudio = data.get('fecha_estudio', '').strip()
    valores       = data.get('valores', {})

    if not tipo_estudio:
        return jsonify({'error': 'Debes seleccionar un tipo de estudio.'}), 400
    if not fecha_estudio:
        return jsonify({'error': 'Debes indicar la fecha del analisis.'}), 400
    if not valores:
        return jsonify({'error': 'Ingresa al menos un valor para analizar.'}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            antecedentes = _cargar_antecedentes(cur, usuario_id)
            condiciones  = _condiciones_activas(antecedentes)

            resumen_ia = generar_resumen(cur, tipo_estudio, valores, antecedentes)
            estado     = calcular_estado(cur, valores, condiciones)

            cur.execute(
                '''INSERT INTO resultados
                   (usuario_id, tipo_estudio, fecha_estudio, valores, resumen_ia, estado)
                   VALUES (%s, %s, %s, %s, %s, %s)''',
                (usuario_id, tipo_estudio, fecha_estudio,
                 json.dumps(valores, ensure_ascii=False), resumen_ia, estado)
            )
            nuevo_id = cur.lastrowid
        conn.commit()

        return jsonify({
            'ok': True,
            'resultado': {
                'id':            nuevo_id,
                'tipo_estudio':  tipo_estudio,
                'fecha_estudio': fecha_estudio,
                'valores':       valores,
                'resumen_ia':    resumen_ia,
                'estado':        estado,
            }
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'error': f'Error al procesar el analisis: {str(e)}'}), 500
    finally:
        conn.close()