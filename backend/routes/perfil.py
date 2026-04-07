from flask import Blueprint, request, jsonify
from db import get_connection
from auth_helpers import login_requerido

perfil_bp = Blueprint('perfil', __name__)


@perfil_bp.route('/perfil', methods=['GET'])
@login_requerido
def obtener_perfil(usuario_id):
    """Retorna los datos del perfil del usuario autenticado."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT nombre, correo, sexo, fecha_nac FROM usuarios WHERE id = %s',
                (usuario_id,)
            )
            usuario = cur.fetchone()

        if not usuario:
            return jsonify({'error': 'Usuario no encontrado.'}), 404

        return jsonify({
            'usuario': {
                'nombre':    usuario['nombre'],
                'correo':    usuario['correo'],
                'sexo':      usuario['sexo'],
                'fecha_nac': str(usuario['fecha_nac']) if usuario['fecha_nac'] else None,
            }
        }), 200

    except Exception as e:
        return jsonify({'error': 'Error al obtener el perfil.'}), 500
    finally:
        conn.close()


@perfil_bp.route('/perfil', methods=['PUT'])
@login_requerido
def actualizar_perfil(usuario_id):
    """Actualiza los datos del perfil del usuario autenticado."""
    data = request.get_json()

    nombre    = (data.get('nombre') or '').strip()
    correo    = (data.get('correo') or '').strip().lower()
    sexo      = data.get('sexo') or None
    fecha_nac = data.get('fecha_nac') or None

    if not nombre or not correo:
        return jsonify({'error': 'El nombre y el correo son obligatorios.'}), 400
    if '@' not in correo:
        return jsonify({'error': 'El correo electrónico no es válido.'}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Verificar que el correo no esté en uso por otro usuario
            cur.execute(
                'SELECT id FROM usuarios WHERE correo = %s AND id != %s',
                (correo, usuario_id)
            )
            if cur.fetchone():
                return jsonify({'error': 'Ese correo ya está en uso por otra cuenta.'}), 409

            cur.execute(
                '''UPDATE usuarios
                   SET nombre = %s, correo = %s, sexo = %s, fecha_nac = %s
                   WHERE id = %s''',
                (nombre, correo, sexo if sexo else None, fecha_nac if fecha_nac else None, usuario_id)
            )
        conn.commit()
        return jsonify({'ok': True, 'nombre': nombre}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'Error al actualizar el perfil.'}), 500
    finally:
        conn.close()