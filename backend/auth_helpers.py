import jwt
import os
import datetime
from functools import wraps
from flask import request, jsonify
from dotenv import load_dotenv
 
load_dotenv()
 
SECRET_KEY = os.getenv('SECRET_KEY', 'clave_secreta_por_defecto')
 
def generar_token(usuario_id):
    """Genera un token JWT válido por 8 horas."""
    payload = {
        'usuario_id': usuario_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
 
def verificar_token(token):
    """Decodifica y valida un token JWT. Retorna el payload o None."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
 
def login_requerido(f):
    """Decorador que protege rutas. Inyecta usuario_id en kwargs."""
    @wraps(f)
    def decorada(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'error': 'Token no proporcionado'}), 401
 
        token = auth.split(' ')[1]
        payload = verificar_token(token)
        if not payload:
            return jsonify({'error': 'Token inválido o expirado'}), 401
 
        kwargs['usuario_id'] = payload['usuario_id']
        return f(*args, **kwargs)
    return decorada
 