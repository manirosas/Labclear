from flask import Blueprint, jsonify
from db import get_connection
from auth_helpers import login_requerido
import json

resultados_bp = Blueprint('resultados', __name__)


@resultados_bp.route('/resultados', methods=['GET'])
@login_requerido
def listar_resultados(usuario_id):
    """Retorna todos los análisis del usuario ordenados del más reciente al más antiguo."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                '''SELECT id, tipo_estudio, fecha_estudio, valores, resumen_ia, estado, creado_en
                   FROM resultados
                   WHERE usuario_id = %s
                   ORDER BY fecha_estudio DESC, creado_en DESC''',
                (usuario_id,)
            )
            rows = cur.fetchall()

        resultados = []
        for r in rows:
            resultados.append({
                'id':            r['id'],
                'tipo_estudio':  r['tipo_estudio'],
                'fecha_estudio': str(r['fecha_estudio']),
                'valores':       json.loads(r['valores']) if isinstance(r['valores'], str) else r['valores'],
                'resumen_ia':    r['resumen_ia'],
                'estado':        r['estado'],
                'creado_en':     str(r['creado_en']),
            })

        return jsonify({'resultados': resultados}), 200

    except Exception as e:
        return jsonify({'error': 'Error al obtener los resultados.'}), 500
    finally:
        conn.close()


@resultados_bp.route('/resultados/<int:resultado_id>', methods=['GET'])
@login_requerido
def obtener_resultado(usuario_id, resultado_id):
    """Retorna un análisis específico verificando que pertenezca al usuario."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                '''SELECT id, tipo_estudio, fecha_estudio, valores, resumen_ia, estado
                   FROM resultados
                   WHERE id = %s AND usuario_id = %s''',
                (resultado_id, usuario_id)
            )
            r = cur.fetchone()

        if not r:
            return jsonify({'error': 'Análisis no encontrado.'}), 404

        resultado = {
            'id':            r['id'],
            'tipo_estudio':  r['tipo_estudio'],
            'fecha_estudio': str(r['fecha_estudio']),
            'valores':       json.loads(r['valores']) if isinstance(r['valores'], str) else r['valores'],
            'resumen_ia':    r['resumen_ia'],
            'estado':        r['estado'],
        }
        return jsonify({'resultado': resultado}), 200

    except Exception as e:
        return jsonify({'error': 'Error al obtener el resultado.'}), 500
    finally:
        conn.close()


@resultados_bp.route('/resultados/<int:resultado_id>', methods=['DELETE'])
@login_requerido
def eliminar_resultado(usuario_id, resultado_id):
    """Elimina un análisis verificando que pertenezca al usuario."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'DELETE FROM resultados WHERE id = %s AND usuario_id = %s',
                (resultado_id, usuario_id)
            )
            eliminados = cur.rowcount
        conn.commit()

        if eliminados == 0:
            return jsonify({'error': 'Análisis no encontrado o sin permiso.'}), 404

        return jsonify({'ok': True}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'Error al eliminar el análisis.'}), 500
    finally:
        conn.close()