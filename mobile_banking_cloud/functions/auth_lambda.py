import json
import boto3
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os
import logging

# Configuración de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clientes AWS
cognito_client = boto3.client('cognito-idp')
dynamodb = boto3.resource('dynamodb')
kms_client = boto3.client('kms')

# Tablas DynamoDB
users_table = dynamodb.Table(os.environ['USERS_TABLE'])
sessions_table = dynamodb.Table(os.environ['SESSIONS_TABLE'])

# Configuración JWT
JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

class AuthenticationError(Exception):
    """Excepción personalizada para errores de autenticación"""
    pass

class AuthorizationError(Exception):
    """Excepción personalizada para errores de autorización"""
    pass

def generate_jwt_token(user_id: str, role: str) -> str:
    """Genera un token JWT para el usuario autenticado"""
    payload = {
        'user_id': user_id,
        'role': role,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verifica y decodifica un token JWT"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token expirado")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Token inválido")

def hash_password(password: str) -> str:
    """Encripta una contraseña usando bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verifica una contraseña contra su hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_user_session(user_id: str, device_info: Dict[str, Any]) -> str:
    """Crea una nueva sesión de usuario"""
    session_id = f"{user_id}_{datetime.utcnow().timestamp()}"
    session_data = {
        'session_id': session_id,
        'user_id': user_id,
        'device_info': device_info,
        'created_at': datetime.utcnow().isoformat(),
        'last_activity': datetime.utcnow().isoformat(),
        'is_active': True
    }
    
    sessions_table.put_item(Item=session_data)
    return session_id

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Función Lambda principal para autenticación y autorización
    Maneja login, registro, verificación de tokens y gestión de sesiones
    """
    try:
        http_method = event['httpMethod']
        path = event['path']
        
        # CORS headers
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
        
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'CORS preflight'})
            }
        
        # Rutas de autenticación
        if path == '/auth/login':
            return handle_login(event, headers)
        elif path == '/auth/register':
            return handle_register(event, headers)
        elif path == '/auth/verify':
            return handle_verify_token(event, headers)
        elif path == '/auth/logout':
            return handle_logout(event, headers)
        elif path == '/auth/refresh':
            return handle_refresh_token(event, headers)
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Endpoint no encontrado'})
            }
            
    except AuthenticationError as e:
        logger.error(f"Error de autenticación: {str(e)}")
        return {
            'statusCode': 401,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
    except AuthorizationError as e:
        logger.error(f"Error de autorización: {str(e)}")
        return {
            'statusCode': 403,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
    except Exception as e:
        logger.error(f"Error interno: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Error interno del servidor'})
        }

def handle_login(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Maneja el proceso de login de usuarios"""
    body = json.loads(event['body'])
    username = body.get('username')
    password = body.get('password')
    device_info = body.get('device_info', {})
    
    if not username or not password:
        raise AuthenticationError("Username y password son requeridos")
    
    # Buscar usuario en DynamoDB
    response = users_table.get_item(Key={'username': username})
    if 'Item' not in response:
        raise AuthenticationError("Credenciales inválidas")
    
    user = response['Item']
    
    # Verificar contraseña
    if not verify_password(password, user['password_hash']):
        raise AuthenticationError("Credenciales inválidas")
    
    # Verificar si el usuario está activo
    if not user.get('is_active', True):
        raise AuthenticationError("Cuenta desactivada")
    
    # Generar token JWT
    token = generate_jwt_token(user['user_id'], user['role'])
    
    # Crear sesión
    session_id = create_user_session(user['user_id'], device_info)
    
    # Actualizar último login
    users_table.update_item(
        Key={'username': username},
        UpdateExpression='SET last_login = :login_time',
        ExpressionAttributeValues={':login_time': datetime.utcnow().isoformat()}
    )
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'message': 'Login exitoso',
            'token': token,
            'session_id': session_id,
            'user': {
                'user_id': user['user_id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role'],
                'last_login': datetime.utcnow().isoformat()
            }
        })
    }

def handle_register(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Maneja el registro de nuevos usuarios"""
    body = json.loads(event['body'])
    username = body.get('username')
    password = body.get('password')
    email = body.get('email')
    full_name = body.get('full_name')
    
    if not all([username, password, email, full_name]):
        raise AuthenticationError("Todos los campos son requeridos")
    
    # Verificar si el usuario ya existe
    response = users_table.get_item(Key={'username': username})
    if 'Item' in response:
        raise AuthenticationError("El usuario ya existe")
    
    # Encriptar contraseña
    password_hash = hash_password(password)
    
    # Crear nuevo usuario
    user_id = f"user_{datetime.utcnow().timestamp()}"
    user_data = {
        'user_id': user_id,
        'username': username,
        'email': email,
        'full_name': full_name,
        'password_hash': password_hash,
        'role': 'customer',  # Rol por defecto
        'is_active': True,
        'created_at': datetime.utcnow().isoformat(),
        'last_login': None
    }
    
    users_table.put_item(Item=user_data)
    
    return {
        'statusCode': 201,
        'headers': headers,
        'body': json.dumps({
            'message': 'Usuario registrado exitosamente',
            'user_id': user_id
        })
    }

def handle_verify_token(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Verifica la validez de un token JWT"""
    auth_header = event.get('headers', {}).get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise AuthenticationError("Token de autorización requerido")
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'message': 'Token válido',
            'user_id': payload['user_id'],
            'role': payload['role']
        })
    }

def handle_logout(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Maneja el logout de usuarios"""
    auth_header = event.get('headers', {}).get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise AuthenticationError("Token de autorización requerido")
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    
    # Desactivar sesión
    sessions_table.update_item(
        Key={'session_id': event.get('headers', {}).get('X-Session-ID', '')},
        UpdateExpression='SET is_active = :inactive',
        ExpressionAttributeValues={':inactive': False}
    )
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({'message': 'Logout exitoso'})
    }

def handle_refresh_token(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Refresca un token JWT válido"""
    auth_header = event.get('headers', {}).get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise AuthenticationError("Token de autorización requerido")
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    
    # Generar nuevo token
    new_token = generate_jwt_token(payload['user_id'], payload['role'])
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'message': 'Token refrescado',
            'token': new_token
        })
    }


