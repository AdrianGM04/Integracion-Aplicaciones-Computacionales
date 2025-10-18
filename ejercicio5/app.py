from datetime import datetime, timedelta, timezone
import os
import uuid

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_mysqldb import MySQL
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    get_jwt, get_jwt_identity, jwt_required
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import MySQLdb.cursors

# -------------------------
# Configuración base
# -------------------------
load_dotenv('config.env')

app = Flask(__name__)

# Flask core
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change_me')

# CORS (abrir a todo, o restringe con lista)
CORS(app, resources={r"/*": {"origins": os.getenv('CORS_ORIGINS', '*')}})

# MariaDB / MySQL
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', '127.0.0.1')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', '3306'))
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'libros_user')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '666')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'JWT03')
app.config['MYSQL_CURSORCLASS'] = os.getenv('MYSQL_CURSORCLASS', 'DictCursor')

mysql = MySQL(app)

# JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt_change_me')
app.config['JWT_ALGORITHM'] = os.getenv('JWT_ALGORITHM', 'HS256')
access_minutes = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES_MIN', '15'))
refresh_days = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES_DAYS', '7'))
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=access_minutes)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=refresh_days)

jwt = JWTManager(app)

# -------------------------
# Utilidades DB
# -------------------------

def dict_cursor():
    return mysql.connection.cursor(MySQLdb.cursors.DictCursor)


def ahora_utc():
    return datetime.now(timezone.utc)


def registrar_token_db(user_id, jti, token_type, session_id, iat, exp, parent_refresh_jti=None):
    cur = dict_cursor()
    cur.execute(
        """
        INSERT INTO jwt_tokens
            (user_id, jti, token_type, session_id, issued_at, expires_at, revoked, parent_refresh_jti)
        VALUES (%s, %s, %s, %s, %s, %s, 0, %s)
        """,
        (user_id, jti, token_type, session_id, iat, exp, parent_refresh_jti)
    )
    mysql.connection.commit()
    cur.close()


def registrar_auditoria(user_id, jti, action, detail=None):
    cur = dict_cursor()
    cur.execute(
        """
        INSERT INTO token_audit (user_id, jti, action, detail, ip, user_agent)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            user_id,
            jti,
            action,
            detail,
            request.headers.get('X-Forwarded-For', request.remote_addr),
            request.headers.get('User-Agent')[:255] if request.headers.get('User-Agent') else None
        )
    )
    mysql.connection.commit()
    cur.close()


def crear_sesion(user_id):
    session_id = str(uuid.uuid4())
    cur = dict_cursor()
    cur.execute(
        """
        INSERT INTO user_sessions (user_id, session_id, ip, user_agent, created_at, last_used_at, is_active)
        VALUES (%s, %s, %s, %s, UTC_TIMESTAMP(), UTC_TIMESTAMP(), 1)
        """,
        (
            user_id,
            session_id,
            request.headers.get('X-Forwarded-For', request.remote_addr),
            request.headers.get('User-Agent')[:255] if request.headers.get('User-Agent') else None
        )
    )
    mysql.connection.commit()
    cur.close()
    return session_id


def activar_refresh(user_id, jti, session_id):
    cur = dict_cursor()
    cur.execute(
        """
        INSERT INTO refresh_tokens (user_id, jti, session_id, is_active)
        VALUES (%s, %s, %s, 1)
        """,
        (user_id, jti, session_id)
    )
    mysql.connection.commit()
    cur.close()


def revocar_token_por_jti(jti, detalle='revoked manually'):
    cur = dict_cursor()
    cur.execute("UPDATE jwt_tokens SET revoked = 1 WHERE jti = %s", (jti,))
    mysql.connection.commit()
    cur.close()
    registrar_auditoria(None, jti, 'revoked', detalle)


def refresh_activo(jti):
    cur = dict_cursor()
    cur.execute("SELECT is_active FROM refresh_tokens WHERE jti = %s", (jti,))
    row = cur.fetchone()
    cur.close()
    return bool(row and row['is_active'] == 1)


def marcar_refresh_inactivo(jti):
    cur = dict_cursor()
    cur.execute("UPDATE refresh_tokens SET is_active = 0, revoked_at = UTC_TIMESTAMP() WHERE jti = %s", (jti,))
    mysql.connection.commit()
    cur.close()


def token_revocado(jti):
    cur = dict_cursor()
    cur.execute("SELECT revoked FROM jwt_tokens WHERE jti = %s", (jti,))
    row = cur.fetchone()
    cur.close()
    return bool(row and row['revoked'] == 1)


# -------------------------
# Callbacks de JWT
# -------------------------

@jwt.token_in_blocklist_loader
def checar_token_revocado(jwt_headers, jwt_payload):
    jti = jwt_payload.get('jti')
    ttype = jwt_payload.get('type')
    # Si está marcado como revocado en DB → bloquear
    if token_revocado(jti):
        return True
    # Para refresh tokens, además verificar que siga activo
    if ttype == 'refresh' and not refresh_activo(jti):
        return True
    return False


# -------------------------
# Endpoints
# -------------------------

@app.get('/health')
def health():
    try:
        cur = dict_cursor()
        cur.execute('SELECT 1 AS ok')
        cur.close()
        return jsonify({
            'status': 'ok',
            'db': 'up',
            'time': ahora_utc().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'status': 'degraded', 'error': str(e)}), 500


@app.post('/register')
def register():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not username or not email or not password:
        return jsonify({'msg': 'username, email y password son obligatorios'}), 400

    # Hash robusto sin la limitante de 72 bytes de bcrypt
    password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

    try:
        cur = dict_cursor()
        cur.execute("SELECT id FROM users WHERE username=%s OR email=%s", (username, email))
        if cur.fetchone():
            cur.close()
            return jsonify({'msg': 'Usuario o email ya existe'}), 409

        cur.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, password_hash)
        )
        mysql.connection.commit()
        new_id = cur.lastrowid
        cur.close()
        return jsonify({'msg': 'Usuario registrado', 'user_id': new_id}), 201
    except Exception as e:
        return jsonify({'msg': 'Error al registrar', 'error': str(e)}), 500


@app.post('/login')
def login():
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    # Log intento (éxito/falla se actualiza abajo con registro separado para simplicidad)
    cur = dict_cursor()
    cur.execute(
        "INSERT INTO login_attempts (username, success, ip, user_agent) VALUES (%s, 0, %s, %s)",
        (
            username,
            request.headers.get('X-Forwarded-For', request.remote_addr),
            request.headers.get('User-Agent')[:255] if request.headers.get('User-Agent') else None
        )
    )
    mysql.connection.commit()
    cur.close()

    cur = dict_cursor()
    cur.execute("SELECT id, username, email, password_hash, role, is_active FROM users WHERE username=%s", (username,))
    user = cur.fetchone()
    cur.close()

    if not user or not user['is_active']:
        return jsonify({'msg': 'Credenciales inválidas'}), 401

    if not check_password_hash(user['password_hash'], password):
        return jsonify({'msg': 'Credenciales inválidas'}), 401

    user_id = user['id']
    session_id = crear_sesion(user_id)

    additional_claims = {
        'username': user['username'],
        'role': user['role']
    }

    access_token = create_access_token(identity=str(user_id), additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=str(user_id), additional_claims={'session_id': session_id, **additional_claims})

    # Extrae metadatos del JWT actual para registrar en DB
    now = ahora_utc()
    access_jwt = get_jwt_from_token(access_token)
    refresh_jwt = get_jwt_from_token(refresh_token)

    registrar_token_db(
        user_id=user_id,
        jti=access_jwt['jti'],
        token_type='access',
        session_id=session_id,
        iat=datetime.fromtimestamp(access_jwt['iat'], tz=timezone.utc),
        exp=datetime.fromtimestamp(access_jwt['exp'], tz=timezone.utc)
    )
    registrar_auditoria(user_id, access_jwt['jti'], 'issued', 'login access')

    registrar_token_db(
        user_id=user_id,
        jti=refresh_jwt['jti'],
        token_type='refresh',
        session_id=session_id,
        iat=datetime.fromtimestamp(refresh_jwt['iat'], tz=timezone.utc),
        exp=datetime.fromtimestamp(refresh_jwt['exp'], tz=timezone.utc)
    )
    activar_refresh(user_id, refresh_jwt['jti'], session_id)
    registrar_auditoria(user_id, refresh_jwt['jti'], 'issued', 'login refresh')

    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in_minutes': access_minutes,
        'session_id': session_id
    }), 200


def get_jwt_from_token(token_str: str) -> dict:
    """Decodifica un JWT sin verificar la revocación (Flask-JWT-Extended internals).
    Usado aquí solo para extraer claims como jti/iat/exp que registramos en DB.
    """
    from flask_jwt_extended.utils import decode_token
    return decode_token(token_str, csrf_value=None, allow_expired=False)


@app.get('/protected')
@jwt_required()
def protected():
    identidad = get_jwt_identity()  # user_id
    claims = get_jwt()
    registrar_auditoria(int(identidad), claims.get('jti'), 'validated', 'protected endpoint')
    return jsonify({
        'msg': 'Acceso concedido',
        'user_id': identidad,
        'claims': {
            'username': claims.get('username'),
            'role': claims.get('role')
        }
    }), 200


@app.post('/refresh')
@jwt_required(refresh=True)
def refresh():
    current_user_id = int(get_jwt_identity())
    claims = get_jwt()
    refresh_jti = claims.get('jti')
    session_id = claims.get('session_id')

    if not refresh_activo(refresh_jti):
        return jsonify({'msg': 'Refresh token inactivo o revocado'}), 401

    additional_claims = {
        'username': claims.get('username'),
        'role': claims.get('role')
    }

    new_access = create_access_token(identity=str(current_user_id), additional_claims=additional_claims)
    access_jwt = get_jwt_from_token(new_access)

    registrar_token_db(
        user_id=current_user_id,
        jti=access_jwt['jti'],
        token_type='access',
        session_id=session_id,
        iat=datetime.fromtimestamp(access_jwt['iat'], tz=timezone.utc),
        exp=datetime.fromtimestamp(access_jwt['exp'], tz=timezone.utc),
        parent_refresh_jti=refresh_jti
    )
    registrar_auditoria(current_user_id, access_jwt['jti'], 'refreshed', f'from refresh {refresh_jti}')

    return jsonify({
        'access_token': new_access,
        'token_type': 'Bearer',
        'expires_in_minutes': access_minutes
    }), 200


@app.post('/logout')
@jwt_required()
def logout():
    claims = get_jwt()
    jti = claims.get('jti')
    revocar_token_por_jti(jti, 'logout')
    return jsonify({'msg': 'Token revocado'}), 200


@app.post('/logout_all')
@jwt_required()
def logout_all():
    # Revoca todos los tokens (access/refresh) de la sesión actual
    claims = get_jwt()
    identidad = int(get_jwt_identity())
    session_id = claims.get('session_id')

    cur = dict_cursor()
    if session_id:
        cur.execute(
            "UPDATE jwt_tokens SET revoked = 1 WHERE user_id=%s AND session_id=%s AND revoked=0",
            (identidad, session_id)
        )
        cur.execute(
            "UPDATE refresh_tokens SET is_active = 0, revoked_at = UTC_TIMESTAMP() WHERE session_id=%s AND is_active=1",
            (session_id,)
        )
        cur.execute(
            "UPDATE user_sessions SET is_active = 0 WHERE session_id=%s",
            (session_id,)
        )
        mysql.connection.commit()
    cur.close()

    registrar_auditoria(identidad, claims.get('jti'), 'revoked', 'logout_all session')
    return jsonify({'msg': 'Sesión cerrada y tokens revocados'}), 200


# -------------------------
# Punto de entrada
# -------------------------
if __name__ == '__main__':
    app.run(host=os.getenv('FLASK_RUN_HOST', '0.0.0.0'), port=int(os.getenv('FLASK_RUN_PORT', '5000')))