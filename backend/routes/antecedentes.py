from flask import Blueprint, request, jsonify
from db import get_connection
from auth_helpers import login_requerido

antecedentes_bp = Blueprint('antecedentes', __name__)

CAMPOS = ['diabetes', 'embarazo', 'hipertension', 'dislipidemia', 'anemia', 'enfermedad_renal']


@antecedentes_bp.route('/antecedentes', methods=['GET'])
@login_requerido
def obtener_antecedentes(usuario_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM antecedentes_clinicos WHERE usuario_id = %s', (usuario_id,))
            row = cur.fetchone()
        if not row:
            return jsonify({'antecedentes': None, 'completado': False}), 200
        for k in ['id', 'usuario_id', 'creado_en']:
            row.pop(k, None)
        return jsonify({'antecedentes': row, 'completado': True}), 200
    except Exception as e:
        return jsonify({'error': 'Error al obtener antecedentes.'}), 500
    finally:
        conn.close()


@antecedentes_bp.route('/antecedentes', methods=['POST'])
@login_requerido
def guardar_antecedentes(usuario_id):
    data   = request.get_json()
    vals   = {c: int(bool(data.get(c, 0))) for c in CAMPOS}

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM antecedentes_clinicos WHERE usuario_id = %s', (usuario_id,))
            existe = cur.fetchone()

            if existe:
                set_clause = ', '.join(f'{c} = %s' for c in CAMPOS)
                cur.execute(
                    f'UPDATE antecedentes_clinicos SET {set_clause} WHERE usuario_id = %s',
                    [vals[c] for c in CAMPOS] + [usuario_id]
                )
            else:
                cols  = ', '.join(CAMPOS)
                phs   = ', '.join(['%s'] * len(CAMPOS))
                cur.execute(
                    f'INSERT INTO antecedentes_clinicos (usuario_id, {cols}) VALUES (%s, {phs})',
                    [usuario_id] + [vals[c] for c in CAMPOS]
                )
            cur.execute('UPDATE usuarios SET cuestionario_completado = 1 WHERE id = %s', (usuario_id,))
        conn.commit()
        return jsonify({'ok': True}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': f'Error al guardar antecedentes: {str(e)}'}), 500
    finally:
        conn.close()