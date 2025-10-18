from datetime import datetime, timedelta, timezone
import os
import uuid
import json
import xml.etree.ElementTree as ET

from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from flask_mysqldb import MySQL
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    get_jwt, get_jwt_identity, jwt_required
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import MySQLdb.cursors
import redis

# -------------------------
# Configuración base
# -------------------------
load_dotenv()

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
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'Libros')
app.config['MYSQL_CURSORCLASS'] = os.getenv('MYSQL_CURSORCLASS', 'DictCursor')

mysql = MySQL(app)

# Redis
redis_host = os.getenv('REDIS_HOST', '127.0.0.1')
redis_port = int(os.getenv('REDIS_PORT', '6379'))
redis_db = int(os.getenv('REDIS_DB', '0'))
redis_password = os.getenv('REDIS_PASSWORD', None)

try:
    redis_client = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        password=redis_password,
        decode_responses=True
    )
    # Test connection
    redis_client.ping()
    print("✅ Redis connection successful")
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
    redis_client = None

# JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt_change_me')
app.config['JWT_ALGORITHM'] = os.getenv('JWT_ALGORITHM', 'HS256')
access_minutes = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES_MIN', '15'))
refresh_days = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES_DAYS', '7'))
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=access_minutes)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=refresh_days)

jwt = JWTManager(app)

# -------------------------
# Utilidades Redis
# -------------------------

def redis_set_token(jti, user_id, token_type, expires_seconds, session_id=None):
    """Almacena token en Redis con TTL"""
    if not redis_client:
        return False
    
    key = f"token:{jti}"
    data = {
        'user_id': str(user_id),
        'token_type': token_type,
        'session_id': session_id or '',
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    try:
        redis_client.setex(key, expires_seconds, json.dumps(data))
        return True
    except Exception as e:
        print(f"Redis set error: {e}")
        return False

def redis_get_token(jti):
    """Obtiene token de Redis"""
    if not redis_client:
        return None
    
    try:
        key = f"token:{jti}"
        data = redis_client.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        print(f"Redis get error: {e}")
        return None

def redis_revoke_token(jti):
    """Revoca token en Redis"""
    if not redis_client:
        return False
    
    try:
        key = f"token:{jti}"
        redis_client.delete(key)
        return True
    except Exception as e:
        print(f"Redis delete error: {e}")
        return False

def redis_revoke_user_tokens(user_id, session_id=None):
    """Revoca todos los tokens de un usuario o sesión específica"""
    if not redis_client:
        return False
    
    try:
        pattern = f"token:*"
        keys = redis_client.keys(pattern)
        revoked_count = 0
        
        for key in keys:
            data = redis_client.get(key)
            if data:
                token_data = json.loads(data)
                if (token_data.get('user_id') == str(user_id) and 
                    (session_id is None or token_data.get('session_id') == session_id)):
                    redis_client.delete(key)
                    revoked_count += 1
        
        return revoked_count
    except Exception as e:
        print(f"Redis revoke user tokens error: {e}")
        return False

def redis_set_session(session_id, user_id, expires_seconds):
    """Almacena sesión en Redis"""
    if not redis_client:
        return False
    
    key = f"session:{session_id}"
    data = {
        'user_id': str(user_id),
        'created_at': datetime.now(timezone.utc).isoformat(),
        'last_used': datetime.now(timezone.utc).isoformat()
    }
    
    try:
        redis_client.setex(key, expires_seconds, json.dumps(data))
        return True
    except Exception as e:
        print(f"Redis session set error: {e}")
        return False

def redis_get_session(session_id):
    """Obtiene sesión de Redis"""
    if not redis_client:
        return None
    
    try:
        key = f"session:{session_id}"
        data = redis_client.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        print(f"Redis session get error: {e}")
        return None

def redis_update_session_last_used(session_id):
    """Actualiza timestamp de último uso de sesión"""
    if not redis_client:
        return False
    
    try:
        key = f"session:{session_id}"
        data = redis_client.get(key)
        if data:
            session_data = json.loads(data)
            session_data['last_used'] = datetime.now(timezone.utc).isoformat()
            ttl = redis_client.ttl(key)
            if ttl > 0:
                redis_client.setex(key, ttl, json.dumps(session_data))
            return True
        return False
    except Exception as e:
        print(f"Redis session update error: {e}")
        return False

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
    
    # Almacenar sesión en Redis también
    session_expires = int(refresh_days * 24 * 60 * 60)  # Convertir días a segundos
    redis_set_session(session_id, user_id, session_expires)
    
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
    # Revocar en DB
    cur = dict_cursor()
    cur.execute("UPDATE jwt_tokens SET revoked = 1 WHERE jti = %s", (jti,))
    mysql.connection.commit()
    cur.close()
    
    # Revocar en Redis
    redis_revoke_token(jti)
    
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
    # Verificar en Redis primero (más rápido)
    if redis_client:
        redis_data = redis_get_token(jti)
        if redis_data is None:  # No existe en Redis = revocado
            return True
    
    # Verificar en DB como respaldo
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
    
    # Verificar en Redis primero
    if redis_client:
        redis_data = redis_get_token(jti)
        if redis_data is None:  # No existe en Redis = revocado
            return True
    
    # Si está marcado como revocado en DB → bloquear
    if token_revocado(jti):
        return True
    
    # Para refresh tokens, además verificar que siga activo
    if ttype == 'refresh' and not refresh_activo(jti):
        return True
    
    return False

# -------------------------
# Endpoints de Autenticación
# -------------------------

@app.get('/health')
def health():
    try:
        cur = dict_cursor()
        cur.execute('SELECT 1 AS ok')
        cur.close()
        
        redis_status = "up" if redis_client and redis_client.ping() else "down"
        
        return jsonify({
            'status': 'ok',
            'db': 'up',
            'redis': redis_status,
            'time': ahora_utc().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'status': 'degraded', 'error': str(e)}), 500

@app.post('/auth/register')
def register():
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not name or not email or not password:
        return jsonify({'msg': 'name, email y password son obligatorios'}), 400

    # Hash robusto
    password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

    try:
        cur = dict_cursor()
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            cur.close()
            return jsonify({'msg': 'Email ya existe'}), 409

        cur.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
            (name, email, password_hash)
        )
        mysql.connection.commit()
        new_id = cur.lastrowid
        cur.close()
        return jsonify({'msg': 'Usuario registrado', 'user_id': new_id}), 201
    except Exception as e:
        return jsonify({'msg': 'Error al registrar', 'error': str(e)}), 500

@app.post('/auth/login')
def login():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    # Log intento
    cur = dict_cursor()
    cur.execute(
        "INSERT INTO login_attempts (email, success, ip, user_agent) VALUES (%s, 0, %s, %s)",
        (
            email,
            request.headers.get('X-Forwarded-For', request.remote_addr),
            request.headers.get('User-Agent')[:255] if request.headers.get('User-Agent') else None
        )
    )
    mysql.connection.commit()
    cur.close()

    cur = dict_cursor()
    cur.execute("SELECT id, name, email, password_hash, role, is_active FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    cur.close()

    if not user or not user['is_active']:
        return jsonify({'msg': 'Credenciales inválidas'}), 401

    if not check_password_hash(user['password_hash'], password):
        return jsonify({'msg': 'Credenciales inválidas'}), 401

    user_id = user['id']
    session_id = crear_sesion(user_id)

    additional_claims = {
        'name': user['name'],
        'email': user['email'],
        'role': user['role']
    }

    access_token = create_access_token(identity=str(user_id), additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=str(user_id), additional_claims={'session_id': session_id, **additional_claims})

    # Extrae metadatos del JWT actual para registrar en DB y Redis
    now = ahora_utc()
    access_jwt = get_jwt_from_token(access_token)
    refresh_jwt = get_jwt_from_token(refresh_token)

    # Registrar en DB
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

    # Registrar en Redis
    access_expires = int(access_minutes * 60)
    refresh_expires = int(refresh_days * 24 * 60 * 60)
    
    redis_set_token(access_jwt['jti'], user_id, 'access', access_expires, session_id)
    redis_set_token(refresh_jwt['jti'], user_id, 'refresh', refresh_expires, session_id)

    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in_minutes': access_minutes,
        'session_id': session_id
    }), 200

def get_jwt_from_token(token_str: str) -> dict:
    """Decodifica un JWT sin verificar la revocación"""
    from flask_jwt_extended.utils import decode_token
    return decode_token(token_str, csrf_value=None, allow_expired=False)

@app.get('/auth/status')
@jwt_required()
def auth_status():
    """Compara JWT local vs Redis"""
    identidad = get_jwt_identity()
    claims = get_jwt()
    jti = claims.get('jti')
    
    # Verificar en Redis
    redis_data = redis_get_token(jti) if redis_client else None
    
    # Verificar en DB
    cur = dict_cursor()
    cur.execute("SELECT * FROM jwt_tokens WHERE jti = %s", (jti,))
    db_data = cur.fetchone()
    cur.close()
    
    # Actualizar último uso de sesión
    session_id = claims.get('session_id')
    if session_id:
        redis_update_session_last_used(session_id)
    
    registrar_auditoria(int(identidad), jti, 'validated', 'status check')
    
    return jsonify({
        'jwt_local': {
            'user_id': identidad,
            'jti': jti,
            'claims': claims
        },
        'redis_status': 'connected' if redis_client else 'disconnected',
        'redis_data': redis_data,
        'db_data': db_data,
        'comparison': {
            'redis_exists': redis_data is not None,
            'db_exists': db_data is not None,
            'consistent': (redis_data is not None) == (db_data is not None)
        }
    }), 200

@app.post('/auth/refresh')
@jwt_required(refresh=True)
def refresh():
    current_user_id = int(get_jwt_identity())
    claims = get_jwt()
    refresh_jti = claims.get('jti')
    session_id = claims.get('session_id')

    if not refresh_activo(refresh_jti):
        return jsonify({'msg': 'Refresh token inactivo o revocado'}), 401

    additional_claims = {
        'name': claims.get('name'),
        'email': claims.get('email'),
        'role': claims.get('role')
    }

    new_access = create_access_token(identity=str(current_user_id), additional_claims=additional_claims)
    access_jwt = get_jwt_from_token(new_access)

    # Registrar en DB
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

    # Registrar en Redis
    access_expires = int(access_minutes * 60)
    redis_set_token(access_jwt['jti'], current_user_id, 'access', access_expires, session_id)

    return jsonify({
        'access_token': new_access,
        'token_type': 'Bearer',
        'expires_in_minutes': access_minutes
    }), 200

@app.post('/auth/logout')
@jwt_required()
def logout():
    claims = get_jwt()
    jti = claims.get('jti')
    revocar_token_por_jti(jti, 'logout')
    return jsonify({'msg': 'Token revocado'}), 200

@app.post('/auth/logout_all')
@jwt_required()
def logout_all():
    """Revoca todos los tokens de la sesión actual"""
    claims = get_jwt()
    identidad = int(get_jwt_identity())
    session_id = claims.get('session_id')

    # Revocar en DB
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

    # Revocar en Redis
    redis_revoke_user_tokens(identidad, session_id)

    registrar_auditoria(identidad, claims.get('jti'), 'revoked', 'logout_all session')
    return jsonify({'msg': 'Sesión cerrada y tokens revocados'}), 200

# -------------------------
# Endpoints de Libros (Protegidos)
# -------------------------

def dict_to_xml(data, root_name='root'):
    """Convierte diccionario a XML"""
    root = ET.Element(root_name)
    
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                item_elem = ET.SubElement(root, 'item')
                for key, value in item.items():
                    elem = ET.SubElement(item_elem, key)
                    elem.text = str(value) if value is not None else ''
    elif isinstance(data, dict):
        for key, value in data.items():
            elem = ET.SubElement(root, key)
            elem.text = str(value) if value is not None else ''
    
    return ET.tostring(root, encoding='unicode')

@app.get('/api/books')
@jwt_required()
def get_all_books():
    """Obtiene todos los libros en formato XML"""
    try:
        cur = dict_cursor()
        cur.execute("SELECT * FROM books ORDER BY titulo")
        books = cur.fetchall()
        cur.close()
        
        # Registrar auditoría
        claims = get_jwt()
        registrar_auditoria(int(get_jwt_identity()), claims.get('jti'), 'validated', 'get all books')
        
        # Convertir a XML
        xml_data = dict_to_xml(books, 'books')
        
        response = make_response(xml_data, 200)
        response.headers['Content-Type'] = 'application/xml'
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.get('/api/books/<isbn>')
@jwt_required()
def get_book_by_isbn(isbn):
    """Obtiene un libro por ISBN"""
    try:
        cur = dict_cursor()
        cur.execute("SELECT * FROM books WHERE isbn = %s", (isbn,))
        book = cur.fetchone()
        cur.close()
        
        if not book:
            return jsonify({'msg': 'Libro no encontrado'}), 404
        
        # Registrar auditoría
        claims = get_jwt()
        registrar_auditoria(int(get_jwt_identity()), claims.get('jti'), 'validated', f'get book {isbn}')
        
        return jsonify(book), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.get('/api/books/format/digital')
@jwt_required()
def get_digital_books():
    """Obtiene todos los libros en formato digital"""
    try:
        cur = dict_cursor()
        cur.execute("SELECT * FROM books WHERE formato IN ('digital', 'ambos') ORDER BY titulo")
        books = cur.fetchall()
        cur.close()
        
        # Registrar auditoría
        claims = get_jwt()
        registrar_auditoria(int(get_jwt_identity()), claims.get('jti'), 'validated', 'get digital books')
        
        return jsonify(books), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.get('/api/books/autor/<autor>')
@jwt_required()
def get_books_by_author(autor):
    """Obtiene todos los libros de un autor"""
    try:
        cur = dict_cursor()
        cur.execute("SELECT * FROM books WHERE autor LIKE %s ORDER BY titulo", (f'%{autor}%',))
        books = cur.fetchall()
        cur.close()
        
        # Registrar auditoría
        claims = get_jwt()
        registrar_auditoria(int(get_jwt_identity()), claims.get('jti'), 'validated', f'get books by author {autor}')
        
        return jsonify(books), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.post('/api/books/create')
@jwt_required()
def create_book():
    """Crea un nuevo libro"""
    data = request.get_json(silent=True) or {}
    
    required_fields = ['isbn', 'titulo', 'autor', 'editorial', 'año_publicacion', 'formato', 'precio']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'msg': f'Campo {field} es obligatorio'}), 400
    
    try:
        cur = dict_cursor()
        cur.execute(
            """
            INSERT INTO books (isbn, titulo, autor, editorial, año_publicacion, formato, precio, stock, descripcion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                data['isbn'],
                data['titulo'],
                data['autor'],
                data['editorial'],
                data['año_publicacion'],
                data['formato'],
                data['precio'],
                data.get('stock', 0),
                data.get('descripcion', '')
            )
        )
        mysql.connection.commit()
        new_id = cur.lastrowid
        cur.close()
        
        # Registrar auditoría
        claims = get_jwt()
        registrar_auditoria(int(get_jwt_identity()), claims.get('jti'), 'validated', f'create book {data["isbn"]}')
        
        return jsonify({'msg': 'Libro creado', 'book_id': new_id}), 201
        
    except Exception as e:
        return jsonify({'msg': 'Error al crear libro', 'error': str(e)}), 500

@app.put('/api/books/update')
@jwt_required()
def update_book():
    """Actualiza un libro existente"""
    data = request.get_json(silent=True) or {}
    isbn = data.get('isbn')
    
    if not isbn:
        return jsonify({'msg': 'ISBN es obligatorio'}), 400
    
    try:
        cur = dict_cursor()
        cur.execute("SELECT id FROM books WHERE isbn = %s", (isbn,))
        if not cur.fetchone():
            cur.close()
            return jsonify({'msg': 'Libro no encontrado'}), 404
        
        # Construir query de actualización dinámicamente
        update_fields = []
        values = []
        
        for field in ['titulo', 'autor', 'editorial', 'año_publicacion', 'formato', 'precio', 'stock', 'descripcion']:
            if field in data:
                update_fields.append(f"{field} = %s")
                values.append(data[field])
        
        if not update_fields:
            cur.close()
            return jsonify({'msg': 'No hay campos para actualizar'}), 400
        
        values.append(isbn)
        query = f"UPDATE books SET {', '.join(update_fields)} WHERE isbn = %s"
        
        cur.execute(query, values)
        mysql.connection.commit()
        cur.close()
        
        # Registrar auditoría
        claims = get_jwt()
        registrar_auditoria(int(get_jwt_identity()), claims.get('jti'), 'validated', f'update book {isbn}')
        
        return jsonify({'msg': 'Libro actualizado'}), 200
        
    except Exception as e:
        return jsonify({'msg': 'Error al actualizar libro', 'error': str(e)}), 500

@app.delete('/api/books/delete')
@jwt_required()
def delete_book():
    """Elimina un libro por ISBN"""
    data = request.get_json(silent=True) or {}
    isbn = data.get('isbn')
    
    if not isbn:
        return jsonify({'msg': 'ISBN es obligatorio'}), 400
    
    try:
        cur = dict_cursor()
        cur.execute("SELECT id FROM books WHERE isbn = %s", (isbn,))
        if not cur.fetchone():
            cur.close()
            return jsonify({'msg': 'Libro no encontrado'}), 404
        
        cur.execute("DELETE FROM books WHERE isbn = %s", (isbn,))
        mysql.connection.commit()
        cur.close()
        
        # Registrar auditoría
        claims = get_jwt()
        registrar_auditoria(int(get_jwt_identity()), claims.get('jti'), 'validated', f'delete book {isbn}')
        
        return jsonify({'msg': 'Libro eliminado'}), 200
        
    except Exception as e:
        return jsonify({'msg': 'Error al eliminar libro', 'error': str(e)}), 500

# -------------------------
# Punto de entrada
# -------------------------
if __name__ == '__main__':
    app.run(host=os.getenv('FLASK_RUN_HOST', '0.0.0.0'), port=int(os.getenv('FLASK_RUN_PORT', '5000')))
