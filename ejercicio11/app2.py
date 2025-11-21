from datetime import datetime, timedelta, timezone
import os
import uuid

from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    get_jwt, get_jwt_identity, jwt_required
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import pymysql
import pymysql.cursors

# Swagger UI
from flask_swagger_ui import get_swaggerui_blueprint

# -------------------------
# Configuración base
# -------------------------
load_dotenv('config.env')

app = Flask(__name__)

# Flask core
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change_me')

# CORS (abrir a todo, o restringe con lista)
CORS(app, resources={r"/*": {"origins": os.getenv('CORS_ORIGINS', '*')}})

# MariaDB / MySQL - Configuración para PyMySQL
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', '127.0.0.1')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', '3306'))
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'libros_user')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '666')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'JWT03')

def get_db():
    """Obtiene o crea una conexión a la base de datos"""
    if 'db' not in g:
        try:
            g.db = pymysql.connect(
                host=app.config['MYSQL_HOST'],
                port=app.config['MYSQL_PORT'],
                user=app.config['MYSQL_USER'],
                password=app.config['MYSQL_PASSWORD'],
                database=app.config['MYSQL_DB'],
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
                charset='utf8mb4',
                sql_mode='STRICT_TRANS_TABLES',
                init_command="SET sql_mode='STRICT_TRANS_TABLES'"
            )
        except pymysql.err.OperationalError as e:
            # Si hay error de autenticación, intentar con mysql_native_password
            if 'auth' in str(e).lower() or '2059' in str(e):
                # Reintentar con conexión básica
                g.db = pymysql.connect(
                    host=app.config['MYSQL_HOST'],
                    port=app.config['MYSQL_PORT'],
                    user=app.config['MYSQL_USER'],
                    password=app.config['MYSQL_PASSWORD'],
                    database=app.config['MYSQL_DB'],
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=False
                )
            else:
                raise
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Cierra la conexión a la base de datos al finalizar el request"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

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
    return get_db().cursor()

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
    get_db().commit()
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
    get_db().commit()
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
    get_db().commit()
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
    get_db().commit()
    cur.close()

def revocar_token_por_jti(jti, detalle='revoked manually'):
    cur = dict_cursor()
    cur.execute("UPDATE jwt_tokens SET revoked = 1 WHERE jti = %s", (jti,))
    get_db().commit()
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
    get_db().commit()
    cur.close()

def token_revocado(jti):
    cur = dict_cursor()
    cur.execute("SELECT revoked FROM jwt_tokens WHERE jti = %s", (jti,))
    row = cur.fetchone()
    cur.close()
    return bool(row and row['revoked'] == 1)

def get_jwt_from_token(token_str: str) -> dict:
    """Decodifica un JWT sin verificar la revocación (Flask-JWT-Extended internals).
    Usado aquí solo para extraer claims como jti/iat/exp que registramos en DB.
    """
    from flask_jwt_extended.utils import decode_token
    return decode_token(token_str, csrf_value=None, allow_expired=False)

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
        get_db().commit()
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
    get_db().commit()
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
        get_db().commit()
    cur.close()

    registrar_auditoria(identidad, claims.get('jti'), 'revoked', 'logout_all session')
    return jsonify({'msg': 'Sesión cerrada y tokens revocados'}), 200

# -------------------------
# OpenAPI 3.0 (Swagger UI)
# -------------------------

def build_openapi_spec():
    """
    Genera un documento OpenAPI 3.0.3 en memoria, con servidores relativos para funcionar
    en GCP con IP dinámica (o detrás de un proxy). Los esquemas incluyen ejemplos prácticos.
    """
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "JWT Microservicio (Flask + MySQL/MariaDB)",
            "version": "1.0.0",
            "description": "Autenticación con JWT (access/refresh), sesiones, auditoría y endpoints protegidos."
        },
        # Importante: usar relativo para IP dinámica / proxies
        "servers": [
            {"url": "/"}
        ],
        "tags": [
            {"name": "Health", "description": "Salud del servicio y DB"},
            {"name": "Auth", "description": "Registro, login, refresh y cierre de sesión"},
            {"name": "Protected", "description": "Rutas que requieren JWT válido"}
        ],
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            },
            "schemas": {
                "MessageResponse": {
                    "type": "object",
                    "properties": {"msg": {"type": "string"}},
                    "example": {"msg": "Token revocado"}
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {"msg": {"type": "string"}, "error": {"type": "string"}},
                    "example": {"msg": "Error al registrar", "error": "Duplicate entry ..."}
                },
                "HealthResponse": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "db": {"type": "string"},
                        "time": {"type": "string", "format": "date-time"}
                    },
                    "example": {"status": "ok", "db": "up", "time": "2025-10-21T15:22:33.123456+00:00"}
                },
                "RegisterRequest": {
                    "type": "object",
                    "required": ["username", "email", "password"],
                    "properties": {
                        "username": {"type": "string"},
                        "email": {"type": "string", "format": "email"},
                        "password": {"type": "string", "format": "password"}
                    },
                    "example": {"username": "alice", "email": "alice@example.com", "password": "S3gura!123"}
                },
                "RegisterResponse": {
                    "type": "object",
                    "properties": {"msg": {"type": "string"}, "user_id": {"type": "integer"}},
                    "example": {"msg": "Usuario registrado", "user_id": 42}
                },
                "LoginRequest": {
                    "type": "object",
                    "required": ["username", "password"],
                    "properties": {
                        "username": {"type": "string"},
                        "password": {"type": "string", "format": "password"}
                    },
                    "example": {"username": "alice", "password": "S3gura!123"}
                },
                "TokenPairResponse": {
                    "type": "object",
                    "properties": {
                        "access_token": {"type": "string"},
                        "refresh_token": {"type": "string"},
                        "token_type": {"type": "string", "example": "Bearer"},
                        "expires_in_minutes": {"type": "integer"},
                        "session_id": {"type": "string", "format": "uuid"}
                    }
                },
                "AccessTokenResponse": {
                    "type": "object",
                    "properties": {
                        "access_token": {"type": "string"},
                        "token_type": {"type": "string", "example": "Bearer"},
                        "expires_in_minutes": {"type": "integer"}
                    }
                },
                "ProtectedResponse": {
                    "type": "object",
                    "properties": {
                        "msg": {"type": "string"},
                        "user_id": {"type": "string"},
                        "claims": {
                            "type": "object",
                            "properties": {
                                "username": {"type": "string"},
                                "role": {"type": "string"}
                            }
                        }
                    },
                    "example": {
                        "msg": "Acceso concedido",
                        "user_id": "42",
                        "claims": {"username": "alice", "role": "user"}
                    }
                }
            }
        },
        "paths": {
            "/health": {
                "get": {
                    "tags": ["Health"],
                    "summary": "Estado del servicio",
                    "responses": {
                        "200": {
                            "description": "Servicio y DB activos",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/HealthResponse"}}}
                        },
                        "500": {
                            "description": "Degradado / error",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}
                        }
                    }
                }
            },
            "/register": {
                "post": {
                    "tags": ["Auth"],
                    "summary": "Registrar usuario",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/RegisterRequest"}}
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Usuario creado",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/RegisterResponse"}}}
                        },
                        "400": {"description": "Datos inválidos", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MessageResponse"}}}},
                        "409": {"description": "Conflicto (usuario/email)", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MessageResponse"}}}},
                        "500": {"description": "Error servidor", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}}
                    }
                }
            },
            "/login": {
                "post": {
                    "tags": ["Auth"],
                    "summary": "Login y emisión de tokens",
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/LoginRequest"}}}
                    },
                    "responses": {
                        "200": {
                            "description": "Par de tokens emitidos",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/TokenPairResponse"}}}
                        },
                        "401": {"description": "Credenciales inválidas", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MessageResponse"}}}}
                    }
                }
            },
            "/protected": {
                "get": {
                    "tags": ["Protected"],
                    "summary": "Endpoint protegido",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "Acceso concedido",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ProtectedResponse"}}}
                        },
                        "401": {"description": "No autorizado", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MessageResponse"}}}}
                    }
                }
            },
            "/refresh": {
                "post": {
                    "tags": ["Auth"],
                    "summary": "Emitir nuevo access token usando refresh",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "Nuevo access token emitido",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/AccessTokenResponse"}}}
                        },
                        "401": {"description": "Refresh inactivo o revocado", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MessageResponse"}}}}
                    }
                }
            },
            "/logout": {
                "post": {
                    "tags": ["Auth"],
                    "summary": "Revocar access token actual",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {"description": "Token revocado", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MessageResponse"}}}},
                        "401": {"description": "No autorizado", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MessageResponse"}}}}
                    }
                }
            },
            "/logout_all": {
                "post": {
                    "tags": ["Auth"],
                    "summary": "Cerrar sesión completa (revoca tokens de la sesión)",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {"description": "Sesión cerrada y tokens revocados", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MessageResponse"}}}},
                        "401": {"description": "No autorizado", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MessageResponse"}}}}
                    }
                }
            }
        }
    }

# Endpoint que expone el JSON de la especificación
@app.get('/openapi.json')
def openapi_json():
    return jsonify(build_openapi_spec())

# Swagger UI en /docs (consume /openapi.json)
SWAGGER_URL = '/docs'
API_URL = '/openapi.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        "app_name": "JWT Microservicio (Flask)",
        # Opcional: persistir auth en la UI
        "persistAuthorization": True,
        # Por defecto no definimos 'urls' ni 'validatorUrl' para simplicidad
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# -------------------------
# Punto de entrada
# -------------------------
if __name__ == '__main__':
    app.run(host=os.getenv('FLASK_RUN_HOST', '0.0.0.0'), port=int(os.getenv('FLASK_RUN_PORT', '5000')))
