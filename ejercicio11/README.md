# Ejercicio 11 - Sistema de Autenticación JWT con Flask

Sistema completo de autenticación basado en JWT (JSON Web Tokens) con Flask, gestión de sesiones, auditoría, revocación de tokens y documentación OpenAPI/Swagger.

## 🚀 Características

- Autenticación JWT con access y refresh tokens
- Gestión de sesiones por dispositivo
- Auditoría completa de eventos
- Revocación de tokens individual o por sesión
- Base de datos MySQL/MariaDB
- Documentación OpenAPI con Swagger UI
- Hash de contraseñas con PBKDF2

## 📋 Requisitos

- Instancia de GCP Compute Engine
- Python 3.7+
- MySQL 5.7+ o MariaDB 10.3+

## 📁 Archivos del Proyecto

- `app2.py` - Aplicación principal Flask
- `requirements.txt` - Dependencias de Python
- `config.env` - Configuración de la aplicación
- `schema.sql` - Esquema de base de datos
- `setup_gcp.sh` - Script de configuración automática
- `start.sh` - Script de inicio de la aplicación

## 🔧 Despliegue en GCP

### Paso 1: Subir Archivos a GCP

Desde tu máquina local:

```bash
cd ejercicio11
gcloud compute scp --recurse . INSTANCIA_NOMBRE:/opt/jwt-app --zone=ZONA
```

Ejemplo:
```bash
gcloud compute scp --recurse . mi-instancia:/opt/jwt-app --zone=us-central1-a
```

### Paso 2: Conectar por SSH

```bash
gcloud compute ssh INSTANCIA_NOMBRE --zone=ZONA
```

### Paso 3: Configurar la Aplicación

```bash
cd /opt/jwt-app
chmod +x setup_gcp.sh start.sh
./setup_gcp.sh
```

Este script automáticamente:
- Actualiza el sistema
- Instala Python, pip y MySQL
- Crea entorno virtual
- Instala dependencias de Python
- Configura la base de datos

### Paso 4: Configurar Variables de Entorno

Edita `config.env` si necesitas cambiar la configuración:

```bash
nano config.env
```

**Configuración importante:**
```env
# Base de datos
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=libros_user
MYSQL_PASSWORD=TU_PASSWORD_SEGURO
MYSQL_DB=JWT03

# Flask - importante para GCP
FLASK_RUN_HOST=0.0.0.0  # Permite conexiones externas
FLASK_RUN_PORT=5000

# CORS
CORS_ORIGINS=*
```

### Paso 5: Configurar Base de Datos (si no se ejecutó automáticamente)

```bash
sudo mysql < schema.sql
```

O manualmente:

```bash
sudo mysql
```

Dentro de MySQL:
```sql
CREATE DATABASE IF NOT EXISTS JWT03;
CREATE USER IF NOT EXISTS 'libros_user'@'localhost' IDENTIFIED BY '666';
GRANT ALL PRIVILEGES ON JWT03.* TO 'libros_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Luego ejecutar el schema:
```bash
mysql -u libros_user -p JWT03 < schema.sql
```

**Nota para MariaDB:** Si usas MariaDB y obtienes error de sintaxis, usa:
```sql
ALTER USER 'libros_user'@'localhost' IDENTIFIED BY '666';
FLUSH PRIVILEGES;
```

### Paso 6: Configurar Firewall

Permitir tráfico en el puerto 5000:

```bash
# Desde tu máquina local
gcloud compute firewall-rules create allow-jwt-app \
    --allow tcp:5000 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow JWT Flask App"
```

### Paso 7: Iniciar la Aplicación

```bash
cd /opt/jwt-app
./start.sh
```

O manualmente:
```bash
source venv/bin/activate
python3 app2.py
```

**Salida esperada:**
```
 * Serving Flask app 'app2'
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

## 🧪 Probar la Aplicación

### Obtener IP Externa

```bash
gcloud compute instances describe INSTANCIA_NOMBRE --zone=ZONA --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

### Acceder a Swagger UI

Abre en tu navegador: `http://TU_IP_EXTERNA:5000/docs`

### Verificar Conexión a Base de Datos

1. En Swagger UI, busca el endpoint `GET /health`
2. Haz clic en "Try it out" → "Execute"
3. Deberías ver:
   ```json
   {
     "status": "ok",
     "db": "up",
     "time": "2024-..."
   }
   ```

### Probar Flujo Completo

#### 1. Registrar Usuario
- Endpoint: `POST /register`
- Body:
  ```json
  {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
  }
  ```
- Si obtienes error 409, el usuario ya existe (haz login directamente)

#### 2. Hacer Login
- Endpoint: `POST /login`
- Body:
  ```json
  {
    "username": "testuser",
    "password": "testpass123"
  }
  ```
- **IMPORTANTE:** Copia el `access_token` de la respuesta

#### 3. Acceder a Endpoint Protegido
- Endpoint: `GET /protected`
- Haz clic en el botón "Authorize" (🔒) en la parte superior
- Pega el `access_token` que copiaste
- Haz clic en "Authorize" y luego "Close"
- Vuelve a `/protected` y haz clic en "Execute"
- Deberías ver: `{"msg": "Acceso concedido", ...}`

## 📚 Endpoints Disponibles

### Públicos
- `GET /health` - Estado del servicio y base de datos
- `POST /register` - Registro de nuevo usuario
- `POST /login` - Login y obtención de tokens
- `GET /openapi.json` - Especificación OpenAPI 3.0
- `GET /docs` - Interfaz Swagger UI

### Protegidos (requieren JWT)
- `GET /protected` - Endpoint de ejemplo protegido
- `POST /refresh` - Obtener nuevo access token usando refresh token
- `POST /logout` - Revocar el access token actual
- `POST /logout_all` - Cerrar sesión completa

## 🗄️ Estructura de la Base de Datos

- `users` - Información de usuarios
- `user_sessions` - Sesiones activas
- `jwt_tokens` - Registro de tokens JWT
- `refresh_tokens` - Refresh tokens activos
- `token_audit` - Auditoría de eventos
- `login_attempts` - Intentos de login

## 🔒 Seguridad

- Hash de contraseñas: PBKDF2 con SHA-256
- Tokens JWT firmados con HMAC-SHA256
- Revocación de tokens por JTI
- Auditoría completa de eventos
- Validación de tokens en tiempo real

## 🐛 Solución de Problemas

### Error: "apt-get: command not found"
Tu instancia usa CentOS/RHEL. El script `setup_gcp.sh` detecta automáticamente la distribución y usa el gestor de paquetes correcto.

### Error: "ModuleNotFoundError"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "Usuario o email ya existe" (409)
Esto es normal - el usuario ya existe. Simplemente haz login con ese usuario.

### Error de conexión a base de datos
1. Verifica que MySQL esté corriendo: `sudo systemctl status mysql` (o `mysqld`)
2. Verifica credenciales en `config.env`
3. Prueba conexión: `mysql -u libros_user -p JWT03`

### Puerto 5000 no accesible
1. Verifica firewall de GCP
2. Verifica que la app escuche en `0.0.0.0:5000`
3. Verifica reglas de firewall de la instancia

## 📝 Notas

- Tokens de acceso expiran en 15 minutos (configurable en `config.env`)
- Tokens de refresh expiran en 7 días (configurable en `config.env`)
- Todos los eventos se registran en la base de datos
- Para producción, considera usar un servidor WSGI como Gunicorn

## 🎯 URLs de Acceso

Una vez desplegado:
- **API**: `http://TU_IP_EXTERNA:5000`
- **Swagger UI**: `http://TU_IP_EXTERNA:5000/docs`
- **Health Check**: `http://TU_IP_EXTERNA:5000/health`
- **OpenAPI JSON**: `http://TU_IP_EXTERNA:5000/openapi.json`
