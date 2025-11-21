# Ejercicio 12 - Servicio de Gestión de Imágenes con Google Cloud Storage

Servicio REST completo para gestión de imágenes que integra Google Cloud Storage (GCS) para almacenamiento, MySQL/MariaDB para metadatos, autenticación Bearer token y documentación interactiva con Swagger.

## 🚀 Características

- **Almacenamiento en GCS**: Subida y gestión de imágenes en Google Cloud Storage
- **Metadatos en MySQL**: Registro de información de imágenes en base de datos relacional
- **URLs firmadas**: Generación automática de URLs firmadas con expiración (1 hora)
- **Autenticación Bearer Token**: Protección de endpoints con token de API
- **Formatos de respuesta**: Soporte para XML (por defecto) y JSON
- **Documentación Swagger**: Interfaz interactiva para probar endpoints
- **Validación de archivos**: Solo acepta imágenes (PNG, JPG, JPEG, GIF)
- **Límite de tamaño**: Máximo 16 MB por archivo

## 📋 Requisitos

- Python 3.7+
- MySQL 5.7+ o MariaDB 10.3+
- Cuenta de Google Cloud Platform (GCP)
- Bucket de Google Cloud Storage creado
- Service Account de GCP con permisos para GCS

## 📁 Archivos del Proyecto

```
ejercicio12/
├── app.py                      # Aplicación principal Flask
├── requirements.txt            # Dependencias de Python
├── .env                        # Variables de entorno (crear)
├── service-account-key.json    # Credenciales de GCP Service Account
└── README.md                   # Este archivo
```

## 🔧 Configuración

### 1. Crear Bucket en Google Cloud Storage

```bash
# Usando gcloud CLI
gsutil mb -p PROJECT_ID -l LOCATION gs://BUCKET_NAME

# Ejemplo
gsutil mb -p mi-proyecto -l us-central1 gs://mi-bucket-imagenes
```

O desde la consola de GCP:
1. Ve a Cloud Storage → Buckets
2. Crea un nuevo bucket
3. Anota el nombre del bucket

### 2. Crear Service Account

1. Ve a IAM & Admin → Service Accounts
2. Crea un nuevo Service Account
3. Asigna el rol "Storage Object Admin" o "Storage Admin"
4. Genera una clave JSON y descárgala
5. Guarda el archivo como `service-account-key.json` en el directorio del proyecto

### 3. Configurar Variables de Entorno

Crea un archivo `.env` en el directorio del proyecto:

```env
# Flask
SECRET_KEY=tu_secret_key_seguro
MAX_CONTENT_LENGTH=16777216  # 16 MB en bytes

# MySQL/MariaDB
MYSQL_HOST=127.0.0.1
MYSQL_USER=root
MYSQL_PASSWORD=tu_password
MYSQL_DB=images_db

# Google Cloud Storage
GCS_BUCKET=nombre-de-tu-bucket
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json

# Autenticación API
API_TOKEN=tu_token_seguro_aqui
```

**Importante**: 
- Reemplaza `nombre-de-tu-bucket` con el nombre real de tu bucket
- El `API_TOKEN` debe ser una cadena segura (usa un generador de tokens)
- Asegúrate de que `GOOGLE_APPLICATION_CREDENTIALS` apunte al archivo JSON del Service Account

### 4. Configurar Base de Datos

Crea la base de datos y la tabla de metadatos:

```sql
CREATE DATABASE IF NOT EXISTS images_db;

USE images_db;

CREATE TABLE IF NOT EXISTS images_metadata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL UNIQUE,
    uploaded_at DATETIME NOT NULL,
    size_bytes INT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    url_gs VARCHAR(500) NOT NULL,
    url_signed TEXT,
    INDEX idx_filename (filename),
    INDEX idx_uploaded_at (uploaded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

O ejecuta desde la línea de comandos:

```bash
mysql -u root -p < schema.sql
```

(Si tienes un archivo `schema.sql`)

### 5. Instalar Dependencias

```bash
# Crear entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## 🚀 Ejecutar la Aplicación

### Modo Desarrollo

```bash
python app.py
```

La aplicación estará disponible en `http://localhost:5000`

### Modo Producción

Para producción, usa un servidor WSGI como Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📚 Endpoints Disponibles

### Públicos

#### `GET /health`
Verifica el estado del servicio.

**Ejemplo de respuesta (XML):**
```xml
<response>
  <status>ok</status>
</response>
```

**Ejemplo con JSON:**
```bash
curl "http://localhost:5000/health?format=json"
```

#### `GET /view?name=imagen.jpg`
Visualiza una imagen redirigiendo a su URL firmada.

**Parámetros:**
- `name` (requerido): Nombre del archivo
- `format` (opcional): `json` para obtener la URL sin redirección

**Ejemplo:**
```bash
# Redirección directa
curl "http://localhost:5000/view?name=imagen.jpg"

# Obtener URL en JSON
curl "http://localhost:5000/view?name=imagen.jpg&format=json"
```

### Protegidos (requieren Bearer Token)

Todos los siguientes endpoints requieren el header:
```
Authorization: Bearer <API_TOKEN>
```

#### `POST /upload`
Sube una nueva imagen a GCS.

**Headers:**
- `Authorization: Bearer <API_TOKEN>`

**Body:**
- `file`: Archivo de imagen (multipart/form-data)

**Parámetros de query:**
- `format` (opcional): `json` para respuesta en JSON

**Ejemplo con cURL:**
```bash
curl -X POST "http://localhost:5000/upload" \
  -H "Authorization: Bearer tu_token_aqui" \
  -F "file=@/ruta/a/imagen.jpg"
```

**Ejemplo con JSON:**
```bash
curl -X POST "http://localhost:5000/upload?format=json" \
  -H "Authorization: Bearer tu_token_aqui" \
  -F "file=@/ruta/a/imagen.jpg"
```

**Respuesta (XML por defecto):**
```xml
<response>
  <message>uploaded</message>
  <filename>imagen.jpg</filename>
  <size_bytes>123456</size_bytes>
  <mime_type>image/jpeg</mime_type>
  <url_gs>gs://bucket/imagen.jpg</url_gs>
  <url_signed>https://storage.googleapis.com/...</url_signed>
  <uploaded_at_utc>2024-01-15 10:30:00</uploaded_at_utc>
</response>
```

#### `GET /images`
Lista todas las imágenes disponibles con sus URLs firmadas.

**Headers:**
- `Authorization: Bearer <API_TOKEN>`

**Parámetros de query:**
- `format` (opcional): `json` para respuesta en JSON

**Ejemplo:**
```bash
curl "http://localhost:5000/images?format=json" \
  -H "Authorization: Bearer tu_token_aqui"
```

**Respuesta (JSON):**
```json
{
  "images": [
    {
      "filename": "imagen1.jpg",
      "url_signed": "https://storage.googleapis.com/...",
      "uploaded_at_utc": "2024-01-15 10:30:00"
    },
    {
      "filename": "imagen2.png",
      "url_signed": "https://storage.googleapis.com/...",
      "uploaded_at_utc": "2024-01-15 11:00:00"
    }
  ]
}
```

#### `PUT /update?name=imagen.jpg`
Reemplaza el contenido de una imagen existente.

**Headers:**
- `Authorization: Bearer <API_TOKEN>`

**Parámetros de query:**
- `name` (requerido): Nombre del archivo a actualizar
- `format` (opcional): `json` para respuesta en JSON

**Body:**
- `file`: Nuevo archivo de imagen (multipart/form-data)

**Ejemplo:**
```bash
curl -X PUT "http://localhost:5000/update?name=imagen.jpg&format=json" \
  -H "Authorization: Bearer tu_token_aqui" \
  -F "file=@/ruta/a/nueva_imagen.jpg"
```

#### `DELETE /delete?name=imagen.jpg`
Elimina una imagen de GCS y sus metadatos.

**Headers:**
- `Authorization: Bearer <API_TOKEN>`

**Parámetros de query:**
- `name` (requerido): Nombre del archivo a eliminar
- `format` (opcional): `json` para respuesta en JSON

**Ejemplo:**
```bash
curl -X DELETE "http://localhost:5000/delete?name=imagen.jpg?format=json" \
  -H "Authorization: Bearer tu_token_aqui"
```

**Respuesta:**
```json
{
  "message": "deleted",
  "filename": "imagen.jpg"
}
```

## 📖 Documentación Swagger

La aplicación incluye documentación interactiva con Swagger. Accede a:

```
http://localhost:5000/apidocs
```

Desde Swagger UI puedes:
- Ver todos los endpoints disponibles
- Probar cada endpoint directamente
- Ver ejemplos de request/response
- Configurar el token de autenticación

### Configurar Token en Swagger

1. Abre Swagger UI en `/apidocs`
2. Haz clic en el botón "Authorize" (🔒) en la parte superior
3. Ingresa: `Bearer tu_token_aqui`
4. Haz clic en "Authorize" y luego "Close"
5. Ahora puedes probar los endpoints protegidos

## 🗄️ Estructura de la Base de Datos

### Tabla: `images_metadata`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | INT | ID autoincremental (PK) |
| `filename` | VARCHAR(255) | Nombre del archivo (único) |
| `uploaded_at` | DATETIME | Fecha y hora de subida (UTC) |
| `size_bytes` | INT | Tamaño del archivo en bytes |
| `mime_type` | VARCHAR(100) | Tipo MIME (image/png, image/jpeg, etc.) |
| `url_gs` | VARCHAR(500) | URL de GCS (gs://bucket/filename) |
| `url_signed` | TEXT | URL firmada temporal (1 hora) |

## 🔒 Seguridad

- **Autenticación Bearer Token**: Todos los endpoints de modificación requieren token
- **Validación de archivos**: Solo se aceptan extensiones permitidas
- **Límite de tamaño**: Máximo 16 MB por archivo
- **URLs firmadas**: Acceso temporal con expiración de 1 hora
- **Sanitización de nombres**: Uso de `secure_filename()` para prevenir path traversal

## 📝 Formatos de Respuesta

### XML (Por defecto)

Todas las respuestas son XML por defecto, excepto cuando se especifica `?format=json`.

**Ejemplo:**
```xml
<response>
  <message>uploaded</message>
  <filename>imagen.jpg</filename>
</response>
```

### JSON

Agrega `?format=json` a cualquier endpoint para obtener respuesta en JSON.

**Ejemplo:**
```bash
curl "http://localhost:5000/health?format=json"
```

## 🐛 Solución de Problemas

### Error: "Falta variable de entorno GCS_BUCKET"

**Solución:**
- Verifica que el archivo `.env` existe
- Asegúrate de que `GCS_BUCKET` esté definido en `.env`
- Verifica que el archivo `.env` esté en el mismo directorio que `app.py`

### Error: "Could not automatically determine credentials"

**Solución:**
1. Verifica que `GOOGLE_APPLICATION_CREDENTIALS` apunte al archivo JSON correcto
2. Verifica que el archivo `service-account-key.json` existe
3. Verifica que el Service Account tenga permisos en el bucket

```bash
# Verificar variable de entorno
echo $GOOGLE_APPLICATION_CREDENTIALS

# O establecerla manualmente
export GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
```

### Error: "Access denied" o "403 Forbidden"

**Solución:**
- Verifica que el Service Account tenga el rol "Storage Object Admin" o "Storage Admin"
- Verifica que el bucket existe y el nombre es correcto
- Verifica los permisos del bucket en GCP Console

### Error: "Unauthorized" (401)

**Solución:**
- Verifica que el header `Authorization: Bearer <token>` esté presente
- Verifica que el token coincida con `API_TOKEN` en `.env`
- En Swagger, asegúrate de haber configurado el token en "Authorize"

### Error: "Invalid file type"

**Solución:**
- Solo se aceptan archivos: PNG, JPG, JPEG, GIF
- Verifica la extensión del archivo
- El archivo debe tener una extensión válida

### Error: "File too large"

**Solución:**
- El límite es 16 MB por defecto
- Puedes ajustar `MAX_CONTENT_LENGTH` en `.env` (en bytes)
- Considera comprimir la imagen antes de subirla

### Error de conexión a MySQL

**Solución:**
1. Verifica que MySQL esté corriendo:
   ```bash
   sudo systemctl status mysql
   # o
   sudo systemctl status mariadb
   ```

2. Verifica las credenciales en `.env`

3. Prueba la conexión:
   ```bash
   mysql -u root -p -e "USE images_db; SHOW TABLES;"
   ```

4. Verifica que la tabla `images_metadata` existe

### URLs firmadas expiradas

**Solución:**
- Las URLs firmadas expiran después de 1 hora
- Usa el endpoint `/images` para obtener nuevas URLs firmadas
- O usa `/view?name=imagen.jpg` para generar una nueva URL

## 🔧 Configuración Avanzada

### Cambiar tiempo de expiración de URLs firmadas

Edita la función `generate_signed_url()` en `app.py`:

```python
def generate_signed_url(blob, expiration_hours=1, method='GET'):
    # Cambia expiration_hours al valor deseado
    url = blob.generate_signed_url(
        version='v4',
        expiration=timedelta(hours=24),  # 24 horas
        method=method,
        ...
    )
```

### Agregar más tipos de archivo

Edita `ALLOWED_EXTENSIONS` en `app.py`:

```python
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
```

Y actualiza el `mime_map` en las funciones de upload/update.

### Cambiar límite de tamaño

Edita `MAX_CONTENT_LENGTH` en `.env`:

```env
MAX_CONTENT_LENGTH=33554432  # 32 MB en bytes
```

## 📊 Ejemplo de Flujo Completo

```bash
# 1. Verificar salud del servicio
curl "http://localhost:5000/health?format=json"

# 2. Subir una imagen
curl -X POST "http://localhost:5000/upload?format=json" \
  -H "Authorization: Bearer mi_token_secreto" \
  -F "file=@foto.jpg"

# 3. Listar todas las imágenes
curl "http://localhost:5000/images?format=json" \
  -H "Authorization: Bearer mi_token_secreto"

# 4. Ver una imagen específica
curl "http://localhost:5000/view?name=foto.jpg"

# 5. Actualizar una imagen
curl -X PUT "http://localhost:5000/update?name=foto.jpg&format=json" \
  -H "Authorization: Bearer mi_token_secreto" \
  -F "file=@nueva_foto.jpg"

# 6. Eliminar una imagen
curl -X DELETE "http://localhost:5000/delete?name=foto.jpg?format=json" \
  -H "Authorization: Bearer mi_token_secreto"
```

## 🎯 URLs de Acceso

Una vez desplegado:
- **API Base**: `http://TU_IP:5000`
- **Health Check**: `http://TU_IP:5000/health`
- **Swagger UI**: `http://TU_IP:5000/apidocs`

## 📝 Notas

- Las URLs firmadas expiran después de 1 hora por defecto
- Los metadatos se almacenan en MySQL, pero las imágenes están en GCS
- El formato por defecto es XML, pero puedes usar JSON agregando `?format=json`
- El token de API debe ser seguro y no compartirse públicamente
- Para producción, considera usar variables de entorno del sistema en lugar de `.env`

## 🔗 Referencias

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Google Cloud Storage Python Client](https://cloud.google.com/storage/docs/reference/libraries#client-libraries-install-python)
- [Flasgger (Swagger for Flask)](https://github.com/flasgger/flasgger)
- [Flask-MySQLdb](https://flask-mysqldb.readthedocs.io/)

