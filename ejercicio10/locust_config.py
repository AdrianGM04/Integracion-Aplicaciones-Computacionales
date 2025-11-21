"""
Configuración para Locust
Ejercicio 10 - Integración de Aplicaciones Computacionales
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno si existe un archivo .env
load_dotenv('locust.env', verbose=False)

# Configuración del host del microservicio
# Por defecto usa la IP de GCP proporcionada
LOCUST_HOST = os.getenv('LOCUST_HOST', 'http://136.112.218.8:5000')

# Configuración de usuarios y tasa de spawn
# Estos valores se pueden sobrescribir desde la línea de comandos
DEFAULT_USERS = int(os.getenv('LOCUST_USERS', '10'))  # Número de usuarios simultáneos
DEFAULT_SPAWN_RATE = float(os.getenv('LOCUST_SPAWN_RATE', '2'))  # Usuarios por segundo
DEFAULT_RUN_TIME = os.getenv('LOCUST_RUN_TIME', None)  # Tiempo de ejecución (ej: "5m", "1h")

# Configuración de la interfaz web de Locust
WEB_HOST = os.getenv('LOCUST_WEB_HOST', '0.0.0.0')
WEB_PORT = int(os.getenv('LOCUST_WEB_PORT', '8089'))

# Configuración de logs
LOG_LEVEL = os.getenv('LOCUST_LOG_LEVEL', 'INFO')

# Headless mode (sin interfaz web)
HEADLESS = os.getenv('LOCUST_HEADLESS', 'false').lower() == 'true'

# Configuración de exportación de resultados
EXPORT_HTML = os.getenv('LOCUST_EXPORT_HTML', 'true').lower() == 'true'
EXPORT_CSV = os.getenv('LOCUST_EXPORT_CSV', 'true').lower() == 'true'
RESULTS_DIR = os.getenv('LOCUST_RESULTS_DIR', 'locust_results')

# Configuración de timeouts
REQUEST_TIMEOUT = float(os.getenv('LOCUST_REQUEST_TIMEOUT', '30'))

# Configuración de certificados SSL (si es necesario)
VERIFY_SSL = os.getenv('LOCUST_VERIFY_SSL', 'true').lower() == 'true'

# Configuración de credenciales de prueba (para usuarios que no se registran)
TEST_USERNAME = os.getenv('TEST_USERNAME', 'testuser')
TEST_PASSWORD = os.getenv('TEST_PASSWORD', 'testpass123')

# Configuración de espera entre requests (puede ser sobrescrita en locustfile)
MIN_WAIT = float(os.getenv('LOCUST_MIN_WAIT', '1'))
MAX_WAIT = float(os.getenv('LOCUST_MAX_WAIT', '3'))


def print_config():
    """Imprime la configuración actual"""
    print("\n" + "="*60)
    print("📋 CONFIGURACIÓN DE LOCUST")
    print("="*60)
    print(f"Host: {LOCUST_HOST}")
    print(f"Usuarios por defecto: {DEFAULT_USERS}")
    print(f"Tasa de spawn: {DEFAULT_SPAWN_RATE} usuarios/segundo")
    print(f"Tiempo de ejecución: {DEFAULT_RUN_TIME or 'Indefinido'}")
    print(f"Interfaz web: http://{WEB_HOST}:{WEB_PORT}")
    print(f"Modo headless: {HEADLESS}")
    print(f"Timeout de requests: {REQUEST_TIMEOUT}s")
    print(f"Verificar SSL: {VERIFY_SSL}")
    print("="*60 + "\n")


if __name__ == '__main__':
    print_config()



