# Ejercicio 10 - Pruebas de Rendimiento con Locust

Este ejercicio implementa pruebas de rendimiento para el microservicio JWT utilizando Locust.

## 📋 Descripción

Se realizan pruebas de carga y rendimiento de todos los endpoints del microservicio de autenticación JWT:

- `GET /health` - Verificación de estado
- `POST /register` - Registro de usuarios
- `POST /login` - Autenticación y obtención de tokens
- `GET /protected` - Endpoint protegido (requiere JWT)
- `POST /refresh` - Renovación de access token
- `POST /logout` - Cierre de sesión
- `POST /logout_all` - Cierre de todas las sesiones

## 📁 Estructura de Archivos

```
ejercicio10/
├── app.py                      # Microservicio Flask JWT
├── config.env                  # Configuración del microservicio
├── locustfile.py               # Archivo principal de Locust con las pruebas
├── locust_config.py            # Configuración de Locust
├── test_connection.py          # Script de diagnóstico de conectividad
├── requirements.txt            # Dependencias para Locust
├── requirements_microservice.txt  # Dependencias del microservicio
├── locust.env.example          # Ejemplo de configuración de Locust
├── run_locust.sh               # Script para ejecutar Locust fácilmente
└── results/                    # Directorio para resultados de pruebas
```

## 🚀 Configuración Inicial

### 1. Instalar Dependencias

```bash
# Dependencias para Locust
pip install -r requirements.txt

# Dependencias para el microservicio
pip install -r requirements_microservice.txt
```

### 2. Configurar Base de Datos

El microservicio requiere MySQL/MariaDB. Ejecuta el schema SQL:

```bash
# Si tienes el schema.sql en ejercicio11
mysql -u root -p < ../ejercicio11/schema.sql

# O si está en otro lugar, ajusta la ruta
mysql -u root -p < ruta/al/schema.sql
```

### 3. Configurar el Microservicio

El archivo `config.env` ya está configurado con valores por defecto. Si necesitas cambiarlos:

```env
# Base de datos MySQL/MariaDB
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=libros_user
MYSQL_PASSWORD=666
MYSQL_DB=JWT03

# Flask
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5000
CORS_ORIGINS=*

# JWT
SECRET_KEY=tu_secret_key
JWT_SECRET_KEY=tu_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRES_MIN=15
JWT_REFRESH_TOKEN_EXPIRES_DAYS=7
```

### 4. Configurar Locust (Opcional)

Copia `locust.env.example` a `locust.env` y ajusta según necesites:

```bash
cp locust.env.example locust.env
```

## 🎯 Ejecutar el Microservicio

### Iniciar el Microservicio

```bash
python3 app.py
```

El microservicio estará disponible en `http://0.0.0.0:5000`

### Verificar que Funciona

```bash
curl http://localhost:5000/health
```

Deberías ver:
```json
{
  "status": "ok",
  "db": "up",
  "time": "2024-..."
}
```

### Ejecutar en Background

```bash
# Opción 1: Usando nohup
nohup python3 app.py > microservice.log 2>&1 &

# Opción 2: Usando screen
screen -S microservice
python3 app.py
# Presiona Ctrl+A luego D para detach
```

### Detener el Microservicio

```bash
# Encontrar el proceso
ps aux | grep "python.*app.py"

# Matar el proceso
kill <PID>

# O matar todos los procesos de Flask
pkill -f "python.*app.py"
```

## 🌐 Configuración de Red en GCP

### Abrir Puerto 5000 en el Firewall

```bash
# Usando gcloud (desde tu máquina local)
gcloud compute firewall-rules create allow-flask-5000 \
  --allow tcp:5000 \
  --source-ranges 0.0.0.0/0 \
  --description "Allow Flask microservice on port 5000"
```

### Abrir Puerto 8089 para Locust (Opcional)

```bash
gcloud compute firewall-rules create allow-locust \
  --allow tcp:8089 \
  --source-ranges 0.0.0.0/0 \
  --description "Allow Locust web interface"
```

## 🧪 Ejecutar Pruebas de Rendimiento

### Modo Interactivo (con interfaz web)

```bash
locust -f locustfile.py --host=http://136.112.218.8:5000
```

Luego abre tu navegador en `http://localhost:8089` (o `http://<IP_GCP>:8089` si estás en GCP) y configura:
- **Number of users**: Número de usuarios simultáneos
- **Spawn rate**: Usuarios por segundo
- **Host**: `http://136.112.218.8:5000`

### Modo Headless (sin interfaz web)

```bash
# Prueba rápida (1 minuto, 5 usuarios)
locust -f locustfile.py \
  --host=http://136.112.218.8:5000 \
  --users=5 \
  --spawn-rate=1 \
  --run-time=1m \
  --headless \
  --html=results/quick_test.html

# Prueba de carga media (10 minutos, 50 usuarios)
locust -f locustfile.py \
  --host=http://136.112.218.8:5000 \
  --users=50 \
  --spawn-rate=5 \
  --run-time=10m \
  --headless \
  --html=results/load_test.html \
  --csv=results/load_test

# Prueba de estrés (30 minutos, 100 usuarios)
locust -f locustfile.py \
  --host=http://136.112.218.8:5000 \
  --users=100 \
  --spawn-rate=10 \
  --run-time=30m \
  --headless \
  --html=results/stress_test.html \
  --csv=results/stress_test
```

### Usando el Script de Ejecución

```bash
# Dar permisos de ejecución
chmod +x run_locust.sh

# Modo interactivo
./run_locust.sh -m interactive

# Prueba rápida
./run_locust.sh -m quick

# Prueba de carga
./run_locust.sh -m load

# Prueba de estrés
./run_locust.sh -m stress
```

## 📊 Tipos de Usuarios Simulados

### MicroserviceUser (principal)
Simula el flujo completo de un usuario:
1. Registro (70% de probabilidad)
2. Login
3. Acceso a endpoints protegidos
4. Renovación de tokens
5. Logout

**Distribución de tareas:**
- `GET /health`: 10 veces más frecuente
- `GET /protected`: 8 veces más frecuente
- `POST /refresh`: 5 veces más frecuente
- `POST /register`: 3 veces más frecuente
- `POST /logout`: 2 veces más frecuente
- `POST /logout_all`: 1 vez

### HealthCheckOnlyUser
Usuario ligero que solo verifica el endpoint `/health`. Útil para pruebas de carga básica.

## 📈 Métricas que se Miden

- **Request Rate**: Peticiones por segundo (RPS)
- **Response Time**: Tiempo de respuesta (min, max, promedio, percentiles)
- **Failure Rate**: Tasa de errores
- **Number of Users**: Usuarios simultáneos
- **Total Requests**: Total de peticiones realizadas

### Interpretación de Resultados

**Response Time (ms):**
- < 100ms: Excelente
- 100-500ms: Bueno
- 500-1000ms: Aceptable
- > 1000ms: Necesita optimización

**Failure Rate:**
- < 1%: Excelente
- 1-5%: Aceptable
- > 5%: Problemas de rendimiento o disponibilidad

**Percentiles:**
- **50th percentile (mediana)**: Tiempo de respuesta típico
- **95th percentile**: 95% de las peticiones son más rápidas
- **99th percentile**: 99% de las peticiones son más rápidas

## 🔍 Diagnóstico de Problemas

### Script de Diagnóstico

Antes de ejecutar Locust, verifica que todo funcione:

```bash
python test_connection.py
```

O con un host personalizado:

```bash
python test_connection.py http://136.112.218.8:5000
```

Este script probará:
1. ✅ Conexión al servidor (`/health`)
2. ✅ Registro de usuario (`/register`)
3. ✅ Login (`/login`)
4. ✅ Endpoint protegido (`/protected`)
5. ✅ Refresh token (`/refresh`)

### Errores Comunes y Soluciones

#### ❌ Error: "Connection refused" o "No se puede conectar al servidor"

**Causas posibles:**
- El microservicio no está corriendo
- La URL es incorrecta
- Problemas de firewall/red

**Solución:**
```bash
# Verifica que el microservicio esté corriendo
curl http://136.112.218.8:5000/health

# Verifica el proceso
ps aux | grep python
netstat -tulpn | grep 5000

# Ejecuta el script de diagnóstico
python test_connection.py
```

#### ❌ Error: "401 Unauthorized" en login

**Causas posibles:**
- El usuario de prueba no existe
- Las credenciales son incorrectas

**Solución:**
```bash
# Crea un usuario de prueba primero
curl -X POST http://136.112.218.8:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@test.com","password":"testpass123"}'
```

#### ❌ Error: "Can't connect to MySQL server"

**Solución:**
```bash
# Verificar que MySQL está corriendo
sudo systemctl status mysql
# o
sudo systemctl status mariadb

# Iniciar si no está corriendo
sudo systemctl start mysql
```

#### ❌ Error: "Access denied for user 'libros_user'"

**Solución:**
```bash
# Verificar que el usuario existe
mysql -u root -p -e "SELECT User, Host FROM mysql.user WHERE User='libros_user';"

# Si no existe, ejecuta el schema.sql
mysql -u root -p < ../ejercicio11/schema.sql
```

#### ❌ Error: "ModuleNotFoundError: No module named 'flask'"

**Solución:**
```bash
# Instalar dependencias
pip install -r requirements_microservice.txt
```

#### ❌ El Servicio No Responde desde Fuera

**Verificaciones:**
1. ✅ El servicio está corriendo: `ps aux | grep python`
2. ✅ El puerto está abierto: `netstat -tulpn | grep 5000`
3. ✅ El firewall de GCP permite el puerto 5000
4. ✅ El servicio está escuchando en `0.0.0.0` (no solo `127.0.0.1`)

**Verificar en config.env:**
```
FLASK_RUN_HOST=0.0.0.0  # NO usar 127.0.0.1
```

#### ❌ Alto porcentaje de errores (>5%)

**Causas posibles:**
- Demasiados usuarios simultáneos
- El servidor está sobrecargado
- Problemas de red

**Solución:**
- Reduce el número de usuarios: `--users=5`
- Aumenta el tiempo de espera entre requests
- Verifica la capacidad del servidor
- Revisa los logs del microservicio

#### ❌ Todas las pruebas fallan

**Pasos de diagnóstico:**

1. **Verifica conectividad básica:**
   ```bash
   curl http://136.112.218.8:5000/health
   ```

2. **Ejecuta el script de diagnóstico:**
   ```bash
   python test_connection.py
   ```

3. **Verifica los logs de Locust:**
   - En la interfaz web, ve a la pestaña "Failures"
   - Revisa los mensajes de error específicos

4. **Verifica que el microservicio esté corriendo:**
   ```bash
   ps aux | grep python
   netstat -tulpn | grep 5000
   ```

5. **Revisa los logs del microservicio:**
   - Busca errores en la consola donde corre Flask
   - Verifica errores de base de datos

## 🔧 Configuración Avanzada

### Variables de Entorno para Locust

Puedes configurar Locust mediante variables de entorno o un archivo `locust.env`:

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `LOCUST_HOST` | URL del microservicio | `http://136.112.218.8:5000` |
| `LOCUST_USERS` | Número de usuarios | `10` |
| `LOCUST_SPAWN_RATE` | Usuarios por segundo | `2` |
| `LOCUST_RUN_TIME` | Tiempo de ejecución | `None` |
| `LOCUST_WEB_HOST` | Host de la interfaz web | `0.0.0.0` |
| `LOCUST_WEB_PORT` | Puerto de la interfaz web | `8089` |
| `LOCUST_HEADLESS` | Modo sin interfaz web | `false` |
| `TEST_USERNAME` | Usuario de prueba | `testuser` |
| `TEST_PASSWORD` | Contraseña de prueba | `testpass123` |

### Ejecutar Locust en GCP

Si ejecutas Locust en una instancia de GCP:

1. Abrir el puerto 8089 en el firewall (ver sección anterior)
2. Ejecutar Locust con el host configurado:
   ```bash
   locust -f locustfile.py \
     --host=http://136.112.218.8:5000 \
     --web-host=0.0.0.0
   ```
3. Acceder desde tu navegador usando la IP externa de la instancia:
   ```
   http://<IP_EXTERNA>:8089
   ```

## 📝 Notas

- Los usuarios simulados generan usernames y emails únicos para evitar conflictos
- Los tokens se renuevan automáticamente cuando expiran
- Las pruebas incluyen manejo de errores y reintentos
- Los resultados se pueden exportar en HTML y CSV
- El microservicio debe estar corriendo antes de ejecutar las pruebas

## ✅ Checklist de Configuración

- [ ] MySQL/MariaDB instalado y corriendo
- [ ] Base de datos creada (schema.sql ejecutado)
- [ ] Usuario `libros_user` creado
- [ ] Archivo `config.env` configurado
- [ ] Dependencias de Python instaladas (ambos requirements.txt)
- [ ] Puerto 5000 abierto en firewall de GCP
- [ ] `FLASK_RUN_HOST=0.0.0.0` en config.env
- [ ] Microservicio corriendo y accesible
- [ ] Pruebas de diagnóstico pasan (`test_connection.py`)

## 🔗 Referencias

- [Documentación de Locust](https://docs.locust.io/)
- [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/)
