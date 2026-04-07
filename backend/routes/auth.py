from flask import Blueprint, request, jsonify
import bcrypt
from db import get_connection
from auth_helpers import generar_token

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    nombre   = (data.get('nombre') or '').strip()
    correo   = (data.get('correo') or '').strip().lower()
    password = (data.get('contrasena') or '')
    sexo     = data.get('sexo') or None
    fecha    = data.get('fecha_nac') or None

    # Validaciones básicas
    if not nombre or not correo or not password:
        return jsonify({'error': 'Nombre, correo y contraseña son obligatorios.'}), 400
    if len(password) < 8:
        return jsonify({'error': 'La contraseña debe tener al menos 8 caracteres.'}), 400
    if '@' not in correo:
        return jsonify({'error': 'El correo electrónico no es válido.'}), 400

    # Hash de contraseña
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Verificar si el correo ya existe
            cur.execute('SELECT id FROM usuarios WHERE correo = %s', (correo,))
            if cur.fetchone():
                return jsonify({'error': 'Ya existe una cuenta con ese correo electrónico.'}), 409

            # Insertar nuevo usuario
            cur.execute(
                '''INSERT INTO usuarios (nombre, correo, contrasena, sexo, fecha_nac, aviso_aceptado)
                   VALUES (%s, %s, %s, %s, %s, 1)''',
                (nombre, correo, hashed, sexo if sexo else None, fecha if fecha else None)
            )
            nuevo_id = cur.lastrowid
        conn.commit()

        token = generar_token(nuevo_id)
        return jsonify({'token': token, 'nombre': nombre}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'Error al crear la cuenta. Intenta de nuevo.'}), 500
    finally:
        conn.close()


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    correo   = (data.get('correo') or '').strip().lower()
    password = (data.get('contrasena') or '')

    if not correo or not password:
        return jsonify({'error': 'Correo y contraseña son obligatorios.'}), 400

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT id, nombre, contrasena FROM usuarios WHERE correo = %s',
                (correo,)
            )
            usuario = cur.fetchone()

        if not usuario:
            return jsonify({'error': 'No existe una cuenta con ese correo.'}), 401

        if not bcrypt.checkpw(password.encode('utf-8'), usuario['contrasena'].encode('utf-8')):
            return jsonify({'error': 'Contraseña incorrecta.'}), 401

        token = generar_token(usuario['id'])
        return jsonify({'token': token, 'nombre': usuario['nombre']}), 200

    except Exception as e:
        return jsonify({'error': 'Error al iniciar sesión. Intenta de nuevo.'}), 500
    finally:
        conn.close()