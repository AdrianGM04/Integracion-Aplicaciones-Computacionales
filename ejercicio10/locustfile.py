"""
Locustfile para pruebas de rendimiento del microservicio JWT
Ejercicio 10 - Integración de Aplicaciones Computacionales
"""

import random
import string
from locust import HttpUser, task, between, events
import json
import logging
import requests

# Configurar logging para ver errores detallados
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MicroserviceUser(HttpUser):
    """
    Usuario simulado que interactúa con el microservicio JWT.
    Simula el flujo completo: registro, login, uso de endpoints protegidos, refresh, logout.
    """
    
    wait_time = between(1, 3)  # Espera entre 1 y 3 segundos entre tareas
    
    def on_start(self):
        """Se ejecuta cuando un usuario inicia su sesión de prueba"""
        self.access_token = None
        self.refresh_token = None
        self.session_id = None
        self.username = None
        self.email = None
        self.password = None
        
        # 70% de usuarios intentan registrarse primero, 30% solo hacen login
        if random.random() < 0.7:
            self.register_user()
        
        # Intentar login (si el registro falló, intenta con credenciales existentes)
        self.login_user()
    
    def generate_random_string(self, length=8):
        """Genera una cadena aleatoria para usernames y emails únicos"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def register_user(self):
        """Registra un nuevo usuario"""
        self.username = f"testuser_{self.generate_random_string()}"
        self.email = f"{self.username}@test.com"
        self.password = "TestPassword123!"
        
        payload = {
            "username": self.username,
            "email": self.email,
            "password": self.password
        }
        
        try:
            with self.client.post(
                "/register",
                json=payload,
                catch_response=True,
                name="POST /register",
                timeout=10
            ) as response:
                if response.status_code in [201, 409]:  # 409 = usuario ya existe (OK para pruebas)
                    response.success()
                elif response.status_code == 0:
                    response.failure("Connection error: Server not reachable")
                else:
                    error_msg = f"Register failed: Status {response.status_code}. Response: {response.text[:200]}"
                    response.failure(error_msg)
                    logger.error(error_msg)
        except Exception as e:
            logger.error(f"Exception during register: {str(e)}")
    
    def login_user(self):
        """Inicia sesión y obtiene tokens"""
        # Si no tenemos credenciales, usar credenciales de prueba por defecto
        if not self.username:
            self.username = "testuser"
            self.password = "testpass123"
        
        payload = {
            "username": self.username,
            "password": self.password
        }
        
        try:
            with self.client.post(
                "/login",
                json=payload,
                catch_response=True,
                name="POST /login",
                timeout=10
            ) as response:
                if response.status_code == 200:
                    try:
                        data = response.json()
                        self.access_token = data.get("access_token")
                        self.refresh_token = data.get("refresh_token")
                        self.session_id = data.get("session_id")
                        
                        if not self.access_token or not self.refresh_token:
                            response.failure(f"Tokens no recibidos en respuesta: {data}")
                            logger.error(f"Login response missing tokens: {data}")
                        else:
                            response.success()
                    except json.JSONDecodeError as e:
                        error_msg = f"Error parsing JSON: {str(e)}. Response: {response.text[:200]}"
                        response.failure(error_msg)
                        logger.error(error_msg)
                    except Exception as e:
                        error_msg = f"Error parsing response: {str(e)}. Response: {response.text[:200]}"
                        response.failure(error_msg)
                        logger.error(error_msg)
                elif response.status_code == 401:
                    error_msg = f"Login failed: Credenciales inválidas (401). Usuario: {self.username}"
                    response.failure(error_msg)
                    logger.warning(error_msg)
                elif response.status_code == 0:
                    error_msg = f"Error de conexión: No se pudo conectar al servidor. Verifica que esté corriendo en {self.client.base_url}"
                    response.failure(error_msg)
                    logger.error(error_msg)
                else:
                    error_msg = f"Login failed: Status {response.status_code}. Response: {response.text[:200]}"
                    response.failure(error_msg)
                    logger.error(error_msg)
        except Exception as e:
            error_msg = f"Excepción durante login: {str(e)}"
            logger.error(error_msg)
            # No podemos usar response.failure aquí porque la excepción ocurrió antes
    
    @task(10)
    def health_check(self):
        """Verifica el estado del servicio (endpoint más frecuente)"""
        with self.client.get(
            "/health",
            catch_response=True,
            name="GET /health",
            timeout=10
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "ok":
                        response.success()
                    else:
                        response.failure(f"Health check returned status: {data.get('status')}")
                except:
                    # Si no es JSON, verificar que al menos sea 200
                    if response.status_code == 200:
                        response.success()
                    else:
                        response.failure(f"Unexpected status: {response.status_code}")
            elif response.status_code == 0:
                response.failure("Connection error: Server not reachable")
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(8)
    def protected_endpoint(self):
        """Accede al endpoint protegido (requiere autenticación)"""
        if not self.access_token:
            return
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        with self.client.get(
            "/protected",
            headers=headers,
            catch_response=True,
            name="GET /protected"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                # Token expirado, intentar refresh
                self.refresh_access_token()
                response.failure("Token expired, attempting refresh")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(5)
    def refresh_access_token(self):
        """Renueva el access token usando el refresh token"""
        if not self.refresh_token:
            return
        
        headers = {
            "Authorization": f"Bearer {self.refresh_token}"
        }
        
        with self.client.post(
            "/refresh",
            headers=headers,
            catch_response=True,
            name="POST /refresh"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.access_token = data.get("access_token")
                    response.success()
                except Exception as e:
                    response.failure(f"Error parsing response: {str(e)}")
            else:
                response.failure(f"Refresh failed: {response.status_code}")
    
    @task(2)
    def logout(self):
        """Cierra sesión (revoca el token actual)"""
        if not self.access_token:
            return
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        with self.client.post(
            "/logout",
            headers=headers,
            catch_response=True,
            name="POST /logout"
        ) as response:
            if response.status_code == 200:
                # Después de logout, hacer login nuevamente para continuar
                self.login_user()
                response.success()
            else:
                response.failure(f"Logout failed: {response.status_code}")
    
    @task(1)
    def logout_all(self):
        """Cierra todas las sesiones del usuario"""
        if not self.access_token:
            return
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        with self.client.post(
            "/logout_all",
            headers=headers,
            catch_response=True,
            name="POST /logout_all"
        ) as response:
            if response.status_code == 200:
                # Después de logout_all, hacer login nuevamente
                self.login_user()
                response.success()
            else:
                response.failure(f"Logout all failed: {response.status_code}")
    
    @task(3)
    def register_new_user(self):
        """Ocasionalmente registra un nuevo usuario durante la prueba"""
        username = f"loadtest_{self.generate_random_string()}"
        email = f"{username}@loadtest.com"
        password = "LoadTest123!"
        
        payload = {
            "username": username,
            "email": email,
            "password": password
        }
        
        with self.client.post(
            "/register",
            json=payload,
            catch_response=True,
            name="POST /register (during test)"
        ) as response:
            if response.status_code in [201, 409]:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


class HealthCheckOnlyUser(HttpUser):
    """
    Usuario ligero que solo verifica el health endpoint.
    Útil para pruebas de carga básica sin autenticación.
    """
    
    wait_time = between(0.5, 2)
    weight = 1  # Menor peso, menos usuarios de este tipo
    
    @task
    def health_check(self):
        """Solo verifica el estado del servicio"""
        self.client.get("/health", name="GET /health (health-only user)")


# Eventos para estadísticas personalizadas
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Se ejecuta cuando inicia la prueba"""
    print("\n" + "="*60)
    print("🚀 INICIANDO PRUEBAS DE RENDIMIENTO CON LOCUST")
    print("="*60)
    print(f"Target: {environment.host}")
    print(f"Usuarios: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print("="*60)
    
    # Verificar conectividad básica
    import requests
    try:
        test_response = requests.get(f"{environment.host}/health", timeout=5)
        print(f"✅ Conexión exitosa al servidor: {test_response.status_code}")
        if test_response.status_code == 200:
            print(f"   Respuesta: {test_response.json()}")
        else:
            print(f"   ⚠️  Advertencia: Status code {test_response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"❌ ERROR: No se puede conectar a {environment.host}")
        print("   Verifica que el microservicio esté corriendo")
    except requests.exceptions.Timeout:
        print(f"❌ ERROR: Timeout al conectar a {environment.host}")
    except Exception as e:
        print(f"⚠️  Advertencia al verificar conexión: {str(e)}")
    
    print("="*60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Se ejecuta cuando termina la prueba"""
    print("\n" + "="*60)
    print("✅ PRUEBAS DE RENDIMIENTO FINALIZADAS")
    print("="*60 + "\n")

