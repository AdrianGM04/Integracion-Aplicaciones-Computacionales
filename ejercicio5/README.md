# Ejercicio 5 - Sistema de Autenticación JWT con Flask

Este proyecto implementa un sistema completo de autenticación basado en JWT (JSON Web Tokens) utilizando Flask, con funcionalidades avanzadas de gestión de sesiones, auditoría y revocación de tokens.

## 🚀 Características

- **Autenticación JWT**: Sistema completo con access y refresh tokens
- **Gestión de Sesiones**: Control de sesiones por dispositivo/dispositivo
- **Auditoría Completa**: Registro de todos los eventos de autenticación
- **Revocación de Tokens**: Capacidad de revocar tokens individuales o por sesión
- **Base de Datos MySQL/MariaDB**: Persistencia completa de usuarios, tokens y auditoría
- **Seguridad Robusta**: Hash de contraseñas con PBKDF2, validación de tokens, etc.

## 📋 Requisitos

- Python 3.7+
- MySQL 5.7+ o MariaDB 10.3+
- pip (gestor de paquetes de Python)

## 🛠️ Instalación

### 1. Clonar el repositorio
```bash
git clone <url-del-repositorio>
cd ejercicio5
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar la base de datos

#### Opción A: Usando el script SQL incluido
```bash
mysql -u root -p < schema.sql
```

#### Opción B: Configuración manual
1. Crear la base de datos `JWT03`
2. Crear el usuario `libros_user` con contraseña `666`
3. Ejecutar el script `schema.sql` para crear las tablas

### 4. Configurar variables de entorno
```bash
cp config.env.example config.env
# Editar config.env con tus configuraciones
```

## ⚙️ Configuración

El archivo `config.env` contiene las siguientes configuraciones:

```env
# Configuración del microservicio
SECRET_KEY=mi_clave_secreta_super_segura_123
JWT_SECRET_KEY=jwt_clave_secreta_456
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRES_MIN=15
JWT_REFRESH_TOKEN_EXPIRES_DAYS=7

# Base de datos MySQL/MariaDB
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=libros_user
MYSQL_PASSWORD=666
MYSQL_DB=JWT03
MYSQL_CURSORCLASS=DictCursor

# Flask
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5001
CORS_ORIGINS=*
```

## 🚀 Ejecución

```bash
python app.py
```

El servidor se ejecutará en `http://localhost:5001` por defecto.

## 📚 API Endpoints

### Autenticación

#### `POST /register`
Registra un nuevo usuario.

**Request:**
```json
{
  "username": "usuario",
  "email": "usuario@ejemplo.com",
  "password": "contraseña123"
}
```

**Response:**
```json
{
  "msg": "Usuario registrado",
  "user_id": 1
}
```

#### `POST /login`
Inicia sesión y obtiene tokens JWT.

**Request:**
```json
{
  "username": "usuario",
  "password": "contraseña123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in_minutes": 15,
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### `POST /refresh`
Renueva el access token usando el refresh token.

**Headers:**
```
Authorization: Bearer <refresh_token>
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in_minutes": 15
}
```

#### `POST /logout`
Revoca el token actual.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "msg": "Token revocado"
}
```

#### `POST /logout_all`
Revoca todos los tokens de la sesión actual.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "msg": "Sesión cerrada y tokens revocados"
}
```

### Endpoints Protegidos

#### `GET /protected`
Endpoint de ejemplo que requiere autenticación.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "msg": "Acceso concedido",
  "user_id": "1",
  "claims": {
    "username": "usuario",
    "role": "user"
  }
}
```

### Monitoreo

#### `GET /health`
Verifica el estado del servicio y la conexión a la base de datos.

**Response:**
```json
{
  "status": "ok",
  "db": "up",
  "time": "2024-01-15T10:30:00.000Z"
}
```

## 🗄️ Estructura de la Base de Datos

### Tablas Principales

- **`users`**: Información de usuarios del sistema
- **`user_sessions`**: Sesiones activas por usuario
- **`jwt_tokens`**: Registro de todos los tokens JWT emitidos
- **`refresh_tokens`**: Refresh tokens activos
- **`token_audit`**: Auditoría de eventos de autenticación
- **`login_attempts`**: Registro de intentos de login

## 🔒 Características de Seguridad

- **Hash de Contraseñas**: PBKDF2 con SHA-256 y salt de 16 bytes
- **Tokens JWT**: Firmados con HMAC-SHA256
- **Revocación de Tokens**: Sistema completo de revocación por JTI
- **Auditoría**: Registro completo de eventos de seguridad
- **Gestión de Sesiones**: Control granular de sesiones por dispositivo
- **Validación de Tokens**: Verificación en tiempo real del estado de tokens

## 🧪 Pruebas

### Usando Postman
Importa la colección `postman_collection.json` en Postman para probar todos los endpoints.

### Pruebas Manuales

1. **Registro de Usuario:**
```bash
curl -X POST http://localhost:5001/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}'
```

2. **Login:**
```bash
curl -X POST http://localhost:5001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'
```

3. **Acceso a Endpoint Protegido:**
```bash
curl -X GET http://localhost:5001/protected \
  -H "Authorization: Bearer <access_token>"
```

## 📊 Monitoreo y Logs

El sistema registra automáticamente:
- Intentos de login (exitosos y fallidos)
- Emisión de tokens
- Uso de tokens
- Revocación de tokens
- Acceso a endpoints protegidos

Consulta las tablas `token_audit` y `login_attempts` para análisis de seguridad.

## 🚨 Solución de Problemas

### Error de Conexión a Base de Datos
- Verificar que MySQL/MariaDB esté ejecutándose
- Confirmar credenciales en `config.env`
- Verificar que la base de datos `JWT03` existe

### Error de JWT
- Verificar `JWT_SECRET_KEY` en configuración
- Confirmar que los tokens no han expirado
- Revisar logs de auditoría para tokens revocados

### Error de CORS
- Verificar configuración `CORS_ORIGINS` en `config.env`
- Para desarrollo, usar `*` (no recomendado para producción)

## 📝 Notas de Desarrollo

- Los access tokens expiran en 15 minutos por defecto
- Los refresh tokens expiran en 7 días por defecto
- Cada sesión tiene un UUID único para identificación
- Los tokens se revocan automáticamente al hacer logout
- El sistema soporta múltiples sesiones por usuario

## 🔄 Próximas Mejoras

- [ ] Rate limiting para endpoints de autenticación
- [ ] Notificaciones por email para eventos de seguridad
- [ ] Dashboard de administración
- [ ] Integración con OAuth2 providers
- [ ] Encriptación de datos sensibles en base de datos

## 📄 Licencia

Este proyecto es parte del curso de Integración de Aplicaciones Computacionales.
