# Microservicio GUI - Consumidor de Endpoints

Esta aplicación proporciona una interfaz gráfica (GUI) desarrollada con Tkinter para consumir todos los endpoints del microservicio de autenticación JWT.

## Características

### 1. Configuración Persistente
- **IP y Puerto**: Configuración editable de la dirección del microservicio
- **URL Base**: Generación automática de la URL base
- **Endpoints**: Configuración de todas las rutas de la API
- **Persistencia**: Los datos se guardan en `microservice_config.ini`

### 2. Semáforo de Estado
- **Verde**: Servicio funcionando correctamente
- **Naranja**: Servicio degradado (con errores)
- **Rojo**: Servicio no disponible
- **Gris**: Estado desconocido
- **Monitoreo automático**: Verificación cada 30 segundos

### 3. Logs de Actividad
- **Registro completo**: Todas las peticiones y respuestas
- **Timestamps**: Marca de tiempo para cada actividad
- **Niveles de log**: INFO, WARNING, ERROR
- **Exportación**: Guardar logs en archivos de texto
- **Limpieza**: Opción para limpiar el historial

### 4. Secciones por Endpoint

#### Health Check (`/health`)
- Verificación del estado del microservicio
- Información de la base de datos
- Método: GET

#### Autenticación
- **Registro** (`/register`): Crear nuevos usuarios
- **Login** (`/login`): Iniciar sesión y obtener tokens
- **Refresh** (`/refresh`): Renovar access token
- **Logout** (`/logout`): Revocar token actual
- **Logout All** (`/logout_all`): Revocar todos los tokens de la sesión

#### Endpoint Protegido (`/protected`)
- Acceso a recurso que requiere autenticación
- Requiere access token válido
- Método: GET

## Instalación y Uso

### Requisitos

#### Para Windows/Mac (con interfaz gráfica):
```bash
pip install -r requirements.txt
python app.py
```

#### Para Linux (servidores sin GUI):
```bash
# Opción 1: Instalación automática
chmod +x install_linux.sh
./install_linux.sh

# Opción 2: Instalación manual
sudo apt-get install python3-tk python3-pip  # Ubuntu/Debian
# o
sudo yum install tkinter python3-pip          # CentOS/RHEL

pip3 install -r requirements.txt
python3 app_cli.py  # Usar versión CLI
```

### Ejecución

#### Versión GUI (Windows/Mac/Linux con GUI):
```bash
python app.py
```

#### Versión CLI (Servidores Linux sin GUI):
```bash
python3 app_cli.py
```

### Configuración Inicial
1. Abrir la pestaña "Configuración"
2. Configurar la IP y puerto del microservicio
3. Hacer clic en "Actualizar URL" y "Guardar Configuración"

### Uso de la Aplicación

#### 1. Verificar Estado del Servicio
- El semáforo muestra el estado actual
- Verificación automática cada 30 segundos
- Botón "Verificar Ahora" para verificación manual

#### 2. Probar Endpoints
- **Health Check**: Verificar estado del servicio
- **Registro**: Crear un nuevo usuario
- **Login**: Iniciar sesión (guarda tokens automáticamente)
- **Refresh**: Renovar access token
- **Logout**: Cerrar sesión actual
- **Logout All**: Cerrar todas las sesiones
- **Protected**: Acceder a endpoint protegido

#### 3. Monitorear Actividad
- Pestaña "Logs de Actividad" muestra todas las operaciones
- Exportar logs para análisis
- Limpiar logs cuando sea necesario

## Estructura del Proyecto

```
ejercicio8/
├── app.py                    # Aplicación GUI (Windows/Mac/Linux con GUI)
├── app_cli.py               # Aplicación CLI (Servidores Linux sin GUI)
├── requirements.txt          # Dependencias
├── install_linux.sh         # Script de instalación para Linux
├── README.md                # Este archivo
└── microservice_config.ini  # Configuración (se crea automáticamente)
```

## Versión CLI (Para Servidores Sin GUI)

La versión CLI (`app_cli.py`) proporciona la misma funcionalidad que la versión GUI pero a través de línea de comandos:

### Características de la Versión CLI:
- ✅ **Menú interactivo** con todas las opciones
- ✅ **Misma funcionalidad** que la versión GUI
- ✅ **Logs en tiempo real** en la consola
- ✅ **Configuración persistente** (mismo archivo de configuración)
- ✅ **Monitoreo continuo** del servicio
- ✅ **Emojis y colores** para mejor experiencia visual
- ✅ **Manejo de errores** robusto

### Uso de la Versión CLI:
```bash
python3 app_cli.py
```

### Menú Principal:
```
🚀 MICROSERVICIO CLI - CONSUMIDOR DE ENDPOINTS
============================================================
📍 Servicio: http://127.0.0.1:5000
🔍 Estado: HEALTHY
============================================================
1. 🔍 Verificar estado del servicio
2. 🏥 Probar endpoint /health
3. 👤 Registrar nuevo usuario
4. 🔐 Iniciar sesión
5. 🔄 Renovar access token
6. 🚪 Cerrar sesión
7. 🚪🚪 Cerrar todas las sesiones
8. 🔒 Acceder a endpoint protegido
9. ⚙️ Configurar servicio
10. 📊 Mostrar estado de autenticación
11. 🔄 Monitoreo continuo
0. ❌ Salir
============================================================
```

## Configuración del Microservicio

La aplicación está diseñada para trabajar con el microservicio del ejercicio 5, que incluye:

- **Base de datos**: MySQL/MariaDB
- **Autenticación**: JWT con access y refresh tokens
- **Endpoints**: 7 endpoints principales
- **CORS**: Habilitado para todas las conexiones

### Endpoints Disponibles

| Endpoint | Método | Descripción | Autenticación |
|----------|--------|-------------|---------------|
| `/health` | GET | Estado del servicio | No |
| `/register` | POST | Registro de usuario | No |
| `/login` | POST | Inicio de sesión | No |
| `/protected` | GET | Recurso protegido | Sí (Access Token) |
| `/refresh` | POST | Renovar token | Sí (Refresh Token) |
| `/logout` | POST | Cerrar sesión | Sí (Access Token) |
| `/logout_all` | POST | Cerrar todas las sesiones | Sí (Access Token) |

## Características Técnicas

### Interfaz de Usuario
- **Framework**: Tkinter (incluido en Python)
- **Estilo**: Tema moderno con colores personalizados
- **Layout**: Notebook con pestañas organizadas
- **Responsive**: Adaptable a diferentes tamaños de ventana

### Gestión de Configuración
- **Archivo**: `microservice_config.ini`
- **Secciones**: SERVICE, ENDPOINTS
- **Persistencia**: Automática al guardar cambios

### Monitoreo y Logs
- **Threading**: Operaciones no bloqueantes
- **Timeouts**: 5-10 segundos para peticiones
- **Error Handling**: Manejo robusto de errores
- **Logging**: Sistema completo de registro

### Seguridad
- **Tokens**: Gestión automática de JWT
- **Headers**: Authorization headers automáticos
- **Passwords**: Campos de contraseña ocultos
- **Sessions**: Gestión de sesiones de usuario

## Solución de Problemas

### Script de Diagnóstico
Para diagnosticar problemas de conectividad, use el script incluido:
```bash
python3 diagnose_service.py [URL]
```

Ejemplo:
```bash
python3 diagnose_service.py http://127.0.0.1:5000
```

### Error de Conexión
1. **Ejecutar diagnóstico**: `python3 diagnose_service.py`
2. Verificar que el microservicio esté ejecutándose
3. Comprobar IP y puerto en la configuración
4. Verificar conectividad de red

### Error de Respuesta Vacía/JSON
Si ve errores como "Expecting value: line 1 column 1 (char 0)":
1. El microservicio puede no estar respondiendo correctamente
2. Verificar logs del microservicio
3. Comprobar configuración de la base de datos
4. Usar el script de diagnóstico para más detalles

### Error de Autenticación
1. Asegurarse de haber hecho login primero
2. Verificar que los tokens no hayan expirado
3. Usar refresh token si es necesario

### Error de Base de Datos
1. Verificar que MySQL/MariaDB esté ejecutándose
2. Comprobar configuración de la base de datos
3. Verificar permisos del usuario de la base de datos

## Desarrollo

### Estructura del Código
- **Clase principal**: `MicroserviceGUI`
- **Métodos de configuración**: Gestión de settings
- **Métodos de UI**: Creación de widgets
- **Métodos de API**: Consumo de endpoints
- **Métodos de logging**: Sistema de logs

### Extensibilidad
- Fácil agregar nuevos endpoints
- Configuración modular
- Sistema de logs extensible
- UI adaptable a nuevos requerimientos
