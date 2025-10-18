# Microservicio de Libros - JWT + Redis

## 📋 Descripción

Microservicio de gestión de libros con autenticación JWT y Redis para gestión de sesiones, tokens y revocación. Todas las rutas están protegidas con JWT e incluye un cliente web completo.

## 🚀 Características

- ✅ **Autenticación JWT** con access/refresh tokens
- ✅ **Integración Redis** para gestión de sesiones y tokens
- ✅ **Base de datos MariaDB** optimizada
- ✅ **API REST** con endpoints protegidos
- ✅ **Cliente Web** moderno y responsive
- ✅ **Gestión de libros** (CRUD completo)
- ✅ **Auditoría** de tokens y sesiones

## 📦 Requisitos

- **Python 3.8+**
- **MariaDB/MySQL 10.3+**
- **Redis 6.0+**
- **Docker** (opcional)

## 🛠️ Instalación Rápida

### Opción 1: Docker (Recomendado)

```bash
# Clonar y navegar al directorio
cd ejercicio6

# Ejecutar con Docker
docker-compose up --build

# La aplicación estará disponible en:
# http://localhost:5000
```

### Opción 2: Instalación Manual

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar base de datos
mysql -u root -p < schema.sql

# 3. Configurar variables de entorno
cp env.example .env
# Editar .env con tus configuraciones

# 4. Ejecutar aplicación
python app.py
```

## 🧪 Pruebas

### Cliente Web
```
http://localhost:5000
```

### API Endpoints
- `GET /health` - Estado del sistema
- `POST /auth/register` - Registro de usuario
- `POST /auth/login` - Inicio de sesión
- `GET /auth/status` - Estado de autenticación
- `POST /auth/refresh` - Renovar token
- `POST /auth/logout` - Cerrar sesión
- `GET /api/books` - Todos los libros (XML)
- `GET /api/books/<ISBN>` - Libro por ISBN
- `GET /api/books/format/digital` - Libros digitales
- `GET /api/books/autor/<autor>` - Libros por autor
- `POST /api/books/create` - Crear libro
- `PUT /api/books/update` - Actualizar libro
- `DELETE /api/books/delete` - Eliminar libro

### Pruebas con Script
```bash
python test_api.py
```

### Pruebas con Postman
1. Importar `postman_collection.json`
2. Configurar `base_url = http://localhost:5000`
3. Ejecutar pruebas

## 📊 Datos de Prueba

### Usuario Administrador
- **Email**: `admin@libros.com`
- **Password**: `admin123`

### Libros de Ejemplo
- Cien años de soledad - Gabriel García Márquez
- El Quijote - Miguel de Cervantes
- 1984 - George Orwell
- El señor de los anillos - J.R.R. Tolkien
- Harry Potter y la piedra filosofal - J.K. Rowling

## 🔧 Configuración

### Variables de Entorno (.env)
```env
SECRET_KEY=tu_clave_secreta
JWT_SECRET_KEY=tu_jwt_secret
MYSQL_HOST=127.0.0.1
MYSQL_USER=libros_user
MYSQL_PASSWORD=666
MYSQL_DB=Libros
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
```

## 📁 Estructura del Proyecto

```
ejercicio6/
├── app.py                 # Aplicación Flask principal
├── requirements.txt       # Dependencias Python
├── schema.sql            # Script de base de datos
├── index.html            # Cliente web
├── styles.css            # Estilos CSS
├── app.js                # JavaScript del cliente
├── postman_collection.json # Colección de Postman
├── test_api.py           # Script de pruebas
├── docker-compose.yml    # Configuración Docker
├── Dockerfile            # Imagen Docker
├── nginx.conf            # Configuración Nginx
├── env.example           # Plantilla de variables
└── README.md             # Este archivo
```

## 🚀 Uso

1. **Iniciar servicios**: `docker-compose up`
2. **Abrir navegador**: `http://localhost:5000`
3. **Registrarse** o usar `admin@libros.com` / `admin123`
4. **Probar funcionalidades** en la interfaz web
5. **Ver logs**: `docker-compose logs -f app`

## 🔒 Seguridad

- Todas las rutas protegidas con JWT
- Tokens almacenados en Redis con TTL
- Revocación de tokens individual y masiva
- Auditoría completa de sesiones
- CORS configurado

## 📞 Soporte

Si tienes problemas:
1. Verificar que MariaDB y Redis estén ejecutándose
2. Revisar logs: `docker-compose logs`
3. Verificar variables de entorno en `.env`
4. Ejecutar script de pruebas: `python test_api.py`

---

**¡Disfruta desarrollando con el microservicio de Libros! 🚀📚**