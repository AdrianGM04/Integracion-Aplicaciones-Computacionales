import os
import io
import datetime
from datetime import timedelta, datetime as dt
from functools import wraps
from urllib.parse import quote

from flask import Flask, request, jsonify, make_response, redirect, url_for
from flasgger import Swagger
from flask_mysqldb import MySQL
from google.cloud import storage
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# -------------------------
# Configuración base
# -------------------------
load_dotenv('.env')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change_me')

# Tamaño máximo 16 MB
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))

# MySQL / MariaDB
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', '127.0.0.1')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'test')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

# GCS
GCS_BUCKET = os.getenv('GCS_BUCKET', '')
if not GCS_BUCKET:
    raise RuntimeError("Falta variable de entorno GCS_BUCKET")


# Auth token
API_TOKEN = os.getenv('API_TOKEN', 'change_token')

# Swagger (Flasgger)
app.config['SWAGGER'] = {
    'title': 'GCS Image Service',
    'uiversion': 3
}
swagger = Swagger(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


# -------------------------
# Utilidades
# -------------------------
def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def require_bearer_token(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get('Authorization', '')
        parts = header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer' and parts[1] == API_TOKEN:
            return f(*args, **kwargs)
        return format_response({'error': 'Unauthorized'}, status=401)
    return wrapper

def to_xml(obj, root='response', item='item'):
    """
    Convierte dict/list en XML muy simple.
    """
    def esc(s):
        return (str(s)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))

    def _node(k, v):
        if isinstance(v, dict):
            return f"<{k}>" + "".join(_node(kk, vv) for kk, vv in v.items()) + f"</{k}>"
        elif isinstance(v, list):
            return f"<{k}>" + "".join(_node(item, vv) for vv in v) + f"</{k}>"
        else:
            return f"<{k}>{esc(v)}</{k}>"

    if isinstance(obj, list):
        body = "".join(_node(item, v) for v in obj)
        return f"<{root}>{body}</{root}>"
    elif isinstance(obj, dict):
        body = "".join(_node(k, v) for k, v in obj.items())
        return f"<{root}>{body}</{root}>"
    else:
        return f"<{root}><{item}>{esc(obj)}</{item}></{root}>"


def format_response(data, status=200):
    """
    Respuesta por defecto XML, opcional JSON con ?format=json
    """
    if request.args.get('format', '').lower() == 'json':
        return jsonify(data), status
    # XML por defecto
    xml = to_xml(data)
    resp = make_response(xml, status)
    resp.headers['Content-Type'] = 'application/xml'
    return resp


def gcs_client() -> storage.Client:
    return storage.Client()  # usa GOOGLE_APPLICATION_CREDENTIALS


def generate_signed_url(blob, expiration_hours=1, method='GET'):
    url = blob.generate_signed_url(
        version='v4',
        expiration=timedelta(hours=expiration_hours),
        method=method,
        response_disposition=f'inline; filename="{quote(blob.name)}"',
        content_type=blob.content_type or 'application/octet-stream'
    )
    return url


# -------------------------
# Rutas
# -------------------------
@app.route('/health', methods=['GET'])
def health():
    """
    Healthcheck
    ---
    get:
      summary: Health check
      responses:
        200:
          description: OK
    """
    return format_response({'status': 'ok'})

@app.route('/upload', methods=['POST'])
@require_bearer_token
def upload():
    """
    Subida de imágenes a GCS
    ---
    post:
      summary: Subir imagen
      consumes:
        - multipart/form-data
      parameters:
        - in: header
          name: Authorization
          required: true
          schema:
            type: string
            example: "Bearer <token>"
        - in: query
          name: format
          schema:
            type: string
            enum: [json]
          description: Responder en JSON (por defecto XML)
        - in: formData
          name: file
          type: file
          required: true
      responses:
        201:
          description: Imagen subida
    """
    if 'file' not in request.files:
        return format_response({'error': 'No file part'}, status=400)

    f = request.files['file']
    if f.filename == '':
        return format_response({'error': 'Empty filename'}, status=400)

    if not allowed_file(f.filename):
        return format_response({'error': 'Invalid file type'}, status=400)

    filename = secure_filename(f.filename)
    file_bytes = f.read()
    size_bytes = len(file_bytes)

    # Cálculo rápido de tipo MIME (mejor si usas python-magic; aquí simple)
    ext = filename.rsplit('.', 1)[1].lower()
    mime_map = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'gif': 'image/gif'}
    mime_type = mime_map.get(ext, 'application/octet-stream')

    # Subir a GCS
    client = gcs_client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(filename)
    blob.upload_from_file(io.BytesIO(file_bytes), content_type=mime_type)

    # Generar URL firmada
    signed_url = generate_signed_url(blob, expiration_hours=1)
    url_gs = f"gs://{GCS_BUCKET}/{filename}"

    # Registrar en DB
    now = dt.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO images_metadata (filename, uploaded_at, size_bytes, mime_type, url_gs, url_signed)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (filename, now, size_bytes, mime_type, url_gs, signed_url))
    mysql.connection.commit()
    cur.close()
    
    return format_response({
        'message': 'uploaded',
        'filename': filename,
        'size_bytes': size_bytes,
        'mime_type': mime_type,
        'url_gs': url_gs,
        'url_signed': signed_url,
        'uploaded_at_utc': now
    }, status=201)


@app.route('/images', methods=['GET'])
@require_bearer_token
def list_images():
    """
    Listado de imágenes (con URL firmada 1h)
    ---
    get:
      summary: Listar imágenes
      parameters:
        - in: header
          name: Authorization
          required: true
          schema:
            type: string
        - in: query
          name: format
          schema:
            type: string
            enum: [json]
      responses:
        200:
          description: Lista de imágenes
    """
    client = gcs_client()
    bucket = client.bucket(GCS_BUCKET)

    items = []
    for blob in bucket.list_blobs():
        signed = generate_signed_url(blob, expiration_hours=1)
        items.append({
            'filename': blob.name,
            'url_signed': signed,
            'uploaded_at_utc': dt.utcfromtimestamp(blob.time_created.timestamp()).strftime('%Y-%m-%d %H:%M:%S') if blob.time_created else None
        })

    return format_response({'images': items}, status=200)

@app.route('/view', methods=['GET'])
def view():
    """
    Visualizar una imagen (redirección a URL firmada 1h)
    ---
    get:
      summary: Visualizar imagen (redirige a URL firmada)
      parameters:
        - in: query
          name: name
          required: true
          schema:
            type: string
        - in: query
          name: format
          schema:
            type: string
            enum: [json]
      responses:
        302:
          description: Redirección a URL firmada
    """
    name = request.args.get('name')
    if not name:
        return format_response({'error': 'Missing name'}, status=400)

    client = gcs_client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(name)
    if not blob.exists():
        return format_response({'error': 'Not found'}, status=404)

    signed = generate_signed_url(blob, expiration_hours=1)
    # Si pidieron JSON explícito, no redirigimos:
    if request.args.get('format', '').lower() == 'json':
        return jsonify({'url_signed': signed})

    return redirect(signed, code=302)

@app.route('/delete', methods=['DELETE'])
@require_bearer_token
def delete():
    """
    Borrar una imagen por nombre
    ---
    delete:
      summary: Borrar imagen
      parameters:
        - in: header
          name: Authorization
          required: true
          schema:
            type: string
        - in: query
          name: name
          required: true
          schema:
            type: string
        - in: query
          name: format
          schema:
            type: string
            enum: [json]
      responses:
        200:
          description: Imagen borrada
    """
    name = request.args.get('name')
    if not name:
        return format_response({'error': 'Missing name'}, status=400)

    client = gcs_client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(name)
    if not blob.exists():
        return format_response({'error': 'Not found'}, status=404)
    
    blob.delete()

    # Eliminar metadatos
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM images_metadata WHERE filename = %s", (name,))
    mysql.connection.commit()
    cur.close()

    return format_response({'message': 'deleted', 'filename': name}, status=200)


@app.route('/update', methods=['PUT'])
@require_bearer_token
def update():
    """
    Reemplazar el contenido de una imagen existente
    ---
    put:
      summary: Actualizar imagen (reemplazo)
      consumes:
        - multipart/form-data
      parameters:
        - in: header
          name: Authorization
          required: true
          schema:
            type: string
        - in: query
          name: name
          required: true
          schema:
            type: string
        - in: formData
          name: file
          type: file
          required: true
          - in: query
          name: format
          schema:
            type: string
            enum: [json]
      responses:
        200:
          description: Imagen reemplazada
    """
    name = request.args.get('name')
    if not name:
        return format_response({'error': 'Missing name'}, status=400)

    if 'file' not in request.files:
        return format_response({'error': 'No file part'}, status=400)

    f = request.files['file']
    if f.filename == '':
        return format_response({'error': 'Empty filename'}, status=400)

    # No cambiamos el nombre; verificamos extensión original/entrante
    if not allowed_file(name) or not allowed_file(f.filename):
        return format_response({'error': 'Invalid file type'}, status=400)

    file_bytes = f.read()
    size_bytes = len(file_bytes)

    ext = name.rsplit('.', 1)[1].lower()
    mime_map = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'gif': 'image/gif'}
    mime_type = mime_map.get(ext, 'application/octet-stream')

    client = gcs_client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(name)
    if not blob.exists():
        return format_response({'error': 'Not found'}, status=404)

    blob.upload_from_file(io.BytesIO(file_bytes), content_type=mime_type)
    signed_url = generate_signed_url(blob, expiration_hours=1)
    now = dt.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    # Actualizar metadatos (si existía; si no, insertar)
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM images_metadata WHERE filename = %s", (name,))
    row = cur.fetchone()
    if row:
        cur.execute("""
            UPDATE images_metadata
               SET uploaded_at = %s, size_bytes = %s, mime_type = %s, url_signed = %s
             WHERE filename = %s
        """, (now, size_bytes, mime_type, signed_url, name))
    else:
        cur.execute("""
            INSERT INTO images_metadata (filename, uploaded_at, size_bytes, mime_type, url_gs, url_signed)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, now, size_bytes, mime_type, f"gs://{GCS_BUCKET}/{name}", signed_url))
    mysql.connection.commit()
    cur.close()

    return format_response({
        'message': 'updated',
        'filename': name,
        'size_bytes': size_bytes,
        'mime_type': mime_type,
        'url_signed': signed_url,
        'updated_at_utc': now
    }, status=200)


if __name__ == '__main__':
    # Ejecutar local: python app.py
    app.run(host='0.0.0.0', port=5000, debug=True)
