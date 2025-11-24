"""
Locust Load Testing File for CMS Medical API with CSV Login Support
-------------------------------------------------------------------

Este archivo ya está completamente modificado para:

✔ Leer usuarios de users.csv (username/email + password)
✔ Elegir un usuario aleatorio para cada usuario virtual
✔ Generar token dinámicamente
✔ Continuar con todos tus escenarios (Admin, Doctor, Paciente)
✔ Mantener TODAS tus tareas tal cual estaban
✔ Mantener eventos y logs

IMPORTANTE:
----------
Tu users.csv debe estar EN LA MISMA CARPETA QUE ESTE ARCHIVO.
Formato sugerido:

username,password
carlos_ramirez,123456
laura_sanchez,123456
dr_roberto,123456
"""

from locust import HttpUser, task, between, events
import random
import csv
import os
from datetime import datetime, timedelta

# ============================================================
# 1. Cargar usuarios desde CSV
# ============================================================

def load_users_from_csv():
    file_path = os.path.join(os.path.dirname(__file__), "users.csv")
    users = []

    if not os.path.exists(file_path):
        print("⚠️ WARNING: users.csv no encontrado. Solo se usará el usuario por defecto.")
        return users

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                users.append(row)

        print(f"📌 CSV cargado correctamente: {len(users)} usuarios")
    except Exception as e:
        print(f"❌ ERROR leyendo users.csv: {e}")

    return users


USERS = load_users_from_csv()


# ============================================================
# 2. Clase base CMSUser con login dinámico desde CSV
# ============================================================

class CMSUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """
        PRIMERO: Logeo diná mico usando un usuario del CSV.
        Si falla, este usuario virtual no continuará tareas.
        """
        self.token = None
        self.user_id = None
        self.username = None
        self.login_successful = False

        # Seleccionar usuario desde CSV
        if USERS:
            selected = random.choice(USERS)
            # El CSV tiene email, pero el login usa username
            # El username se genera como la parte antes del @ del email
            email = selected.get("email") or selected.get("correo") or ""
            username = selected.get("username") or email.split("@")[0] if email else ""
            login_data = {
                "username": username,
                "password": selected.get("password")
            }
        else:
            # Fallback si no existe CSV
            login_data = {
                "username": "carlos_ramirez",
                "password": "password123"
            }

        with self.client.post(
            "/api/auth/login",
            json=login_data,
            catch_response=True,
            name="[1] PRIMERO - Login - Generar Token"
        ) as response:

            if response.status_code == 200:
                try:
                    data = response.json()
                    self.token = data.get("token")
                    self.user_id = data.get("user", {}).get("id")
                    self.username = data.get("user", {}).get("username")

                    if self.token:
                        self.login_successful = True
                        response.success()
                    else:
                        response.failure("⚠️ Token no recibido en respuesta")
                except Exception as e:
                    response.failure(f"❌ Error al procesar respuesta JSON: {e}")
            else:
                response.failure(f"❌ Login falló: código {response.status_code}")

    # --------------------------------------------------------

    def get_headers(self):
        """Devuelve headers con token."""
        if self.token:
            return {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
        return {"Content-Type": "application/json"}

    def is_authenticated(self):
        """Verifica si el login fue exitoso."""
        return self.login_successful and self.token is not None

    # --------------------------------------------------------
    # Tareas globales compartidas
    # --------------------------------------------------------

    @task(3)
    def get_current_user(self):
        if not self.is_authenticated():
            return

        self.client.get(
            "/api/auth/me",
            headers=self.get_headers(),
            name="[2] Get Current User"
        )

    @task(2)
    def health_check(self):
        self.client.get("/health", name="Health Check")

    @task(1)
    def health_database(self):
        self.client.get("/health/database", name="Health Database")


# ============================================================
# 3. ADMIN USER
# ============================================================

class AdminUser(CMSUser):
    weight = 1  # 10%

    @task(5)
    def list_users(self):
        if not self.is_authenticated():
            return
        params = {
            "limit": random.randint(10, 50),
            "offset": 0,
            "search": random.choice(["", "admin", "doctor", "patient"])
        }
        self.client.get("/api/users", headers=self.get_headers(), params=params, name="List Users")

    @task(3)
    def get_user_by_id(self):
        if not self.is_authenticated():
            return
        user_id = random.randint(1, 100)
        self.client.get(f"/api/users/{user_id}", headers=self.get_headers(), name="Get User by ID")

    @task(2)
    def list_patients(self):
        if not self.is_authenticated():
            return
        params = {"limit": random.randint(10, 50), "offset": 0}
        self.client.get("/api/patients", headers=self.get_headers(), params=params, name="List Patients")

    @task(2)
    def list_doctors(self):
        if not self.is_authenticated():
            return
        params = {"limit": random.randint(10, 50), "offset": 0}
        self.client.get("/api/doctors", headers=self.get_headers(), params=params, name="List Doctors")

    @task(4)
    def get_dashboard_kpis(self):
        if not self.is_authenticated():
            return
        self.client.get("/api/dashboard/kpis", headers=self.get_headers(), name="Dashboard KPIs")

    @task(3)
    def get_dashboard_charts(self):
        if not self.is_authenticated():
            return
        self.client.get("/api/dashboard/charts", headers=self.get_headers(), name="Dashboard Charts")

    @task(2)
    def list_appointments(self):
        if not self.is_authenticated():
            return
        fecha_desde = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        fecha_hasta = datetime.now().strftime("%Y-%m-%d")
        params = {
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
        }
        self.client.get("/api/appointments/citas", headers=self.get_headers(), params=params, name="List Appointments")

    @task(2)
    def list_audit_logs(self):
        if not self.is_authenticated():
            return
        params = {"limit": 30, "offset": 0}
        self.client.get("/api/audit", headers=self.get_headers(), params=params, name="List Audit Logs")

    @task(1)
    def get_audit_stats(self):
        if not self.is_authenticated():
            return
        self.client.get("/api/audit/stats", headers=self.get_headers(), name="Audit Stats")


# ============================================================
# 4. DOCTOR USER
# ============================================================

class DoctorUser(CMSUser):
    weight = 3  # 30%

    def on_start(self):
        super().on_start()
        self.doctor_id = random.randint(1, 10)
        self.patient_ids = list(range(1, 50))

    @task(6)
    def list_my_appointments(self):
        if not self.is_authenticated():
            return
        fecha_desde = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        fecha_hasta = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        params = {"fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta, "medico_id": self.doctor_id}
        self.client.get("/api/appointments/citas", headers=self.get_headers(), params=params, name="List My Appointments")

    @task(5)
    def list_consultations(self):
        if not self.is_authenticated():
            return
        patient_id = random.choice(self.patient_ids)
        params = {"paciente_id": patient_id, "limit": random.randint(10, 30)}
        self.client.get("/api/appointments/consultas", headers=self.get_headers(), params=params, name="List Consultations")

    @task(4)
    def get_patient_info(self):
        if not self.is_authenticated():
            return
        patient_id = random.choice(self.patient_ids)
        self.client.get(f"/api/patients/{patient_id}", headers=self.get_headers(), name="Get Patient Info")


# ============================================================
# 5. PATIENT USER
# ============================================================

class PatientUser(CMSUser):
    weight = 6  # 60%

    def on_start(self):
        super().on_start()
        self.patient_id = random.randint(1, 50)

    @task(5)
    def get_my_appointments(self):
        if not self.is_authenticated():
            return
        fecha_desde = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        fecha_hasta = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
        params = {"fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta, "paciente_id": self.patient_id}
        self.client.get("/api/appointments/citas", headers=self.get_headers(), params=params, name="Get My Appointments")


# ============================================================
# 6. EVENT LOGS
# ============================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("🚀 Starting CMS API Load Test")
    print(f"📍 Target host: {environment.host}")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("✅ CMS API Load Test Completed")

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    if exception:
        print(f"❌ Request failed: {name} - {exception}")

