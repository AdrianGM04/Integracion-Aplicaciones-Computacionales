#!/usr/bin/env python3
"""
Script de pruebas para el microservicio de Libros con JWT + Redis
"""

import requests
import json
import time
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:5000"
TEST_USER = {
    "name": "Usuario Test",
    "email": "test@libros.com",
    "password": "password123"
}

class BooksAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        self.session_id = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def make_request(self, method, endpoint, data=None, headers=None, expected_status=None):
        """Realiza una petición HTTP y maneja errores"""
        url = f"{self.base_url}{endpoint}"
        
        if headers is None:
            headers = {}
        
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = requests.delete(url, json=data, headers=headers)
            else:
                raise ValueError(f"Método HTTP no soportado: {method}")
            
            if expected_status and response.status_code != expected_status:
                self.log(f"Error: Esperado {expected_status}, obtenido {response.status_code}", "ERROR")
                self.log(f"Respuesta: {response.text}", "ERROR")
                return None
            
            return response
            
        except requests.exceptions.RequestException as e:
            self.log(f"Error de conexión: {e}", "ERROR")
            return None
    
    def test_health(self):
        """Prueba el endpoint de health check"""
        self.log("=== Probando Health Check ===")
        response = self.make_request("GET", "/health", expected_status=200)
        
        if response:
            data = response.json()
            self.log(f"Health check exitoso: {data}")
            return True
        return False
    
    def test_register(self):
        """Prueba el registro de usuario"""
        self.log("=== Probando Registro ===")
        response = self.make_request("POST", "/auth/register", data=TEST_USER, expected_status=201)
        
        if response:
            data = response.json()
            self.log(f"Registro exitoso: {data}")
            return True
        return False
    
    def test_login(self):
        """Prueba el login de usuario"""
        self.log("=== Probando Login ===")
        login_data = {
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
        
        response = self.make_request("POST", "/auth/login", data=login_data, expected_status=200)
        
        if response:
            data = response.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
            self.session_id = data["session_id"]
            self.log(f"Login exitoso: {data}")
            return True
        return False
    
    def test_auth_status(self):
        """Prueba el endpoint de estado de autenticación"""
        self.log("=== Probando Estado de Autenticación ===")
        response = self.make_request("GET", "/auth/status", expected_status=200)
        
        if response:
            data = response.json()
            self.log(f"Estado de autenticación: {json.dumps(data, indent=2)}")
            return True
        return False
    
    def test_get_all_books(self):
        """Prueba obtener todos los libros (XML)"""
        self.log("=== Probando Obtener Todos los Libros (XML) ===")
        response = self.make_request("GET", "/api/books", expected_status=200)
        
        if response:
            self.log(f"Libros obtenidos (XML): {len(response.text)} caracteres")
            self.log(f"Content-Type: {response.headers.get('Content-Type')}")
            return True
        return False
    
    def test_get_book_by_isbn(self):
        """Prueba obtener un libro por ISBN"""
        self.log("=== Probando Obtener Libro por ISBN ===")
        isbn = "978-84-376-0494-7"
        response = self.make_request("GET", f"/api/books/{isbn}", expected_status=200)
        
        if response:
            data = response.json()
            self.log(f"Libro encontrado: {data['titulo']} por {data['autor']}")
            return True
        return False
    
    def test_get_digital_books(self):
        """Prueba obtener libros digitales"""
        self.log("=== Probando Obtener Libros Digitales ===")
        response = self.make_request("GET", "/api/books/format/digital", expected_status=200)
        
        if response:
            data = response.json()
            self.log(f"Libros digitales encontrados: {len(data)}")
            for book in data:
                self.log(f"  - {book['titulo']} ({book['formato']})")
            return True
        return False
    
    def test_get_books_by_author(self):
        """Prueba obtener libros por autor"""
        self.log("=== Probando Obtener Libros por Autor ===")
        author = "Gabriel García Márquez"
        response = self.make_request("GET", f"/api/books/autor/{author}", expected_status=200)
        
        if response:
            data = response.json()
            self.log(f"Libros de {author}: {len(data)}")
            for book in data:
                self.log(f"  - {book['titulo']}")
            return True
        return False
    
    def test_create_book(self):
        """Prueba crear un nuevo libro"""
        self.log("=== Probando Crear Libro ===")
        book_data = {
            "isbn": "978-84-376-9999-9",
            "titulo": "Libro de Prueba API",
            "autor": "Autor de Prueba",
            "editorial": "Editorial de Prueba",
            "año_publicacion": 2024,
            "formato": "digital",
            "precio": 19.99,
            "stock": 10,
            "descripcion": "Libro creado mediante script de pruebas"
        }
        
        response = self.make_request("POST", "/api/books/create", data=book_data, expected_status=201)
        
        if response:
            data = response.json()
            self.log(f"Libro creado: {data}")
            return True
        return False
    
    def test_update_book(self):
        """Prueba actualizar un libro"""
        self.log("=== Probando Actualizar Libro ===")
        update_data = {
            "isbn": "978-84-376-9999-9",
            "titulo": "Libro de Prueba API - Actualizado",
            "precio": 24.99,
            "stock": 15
        }
        
        response = self.make_request("PUT", "/api/books/update", data=update_data, expected_status=200)
        
        if response:
            data = response.json()
            self.log(f"Libro actualizado: {data}")
            return True
        return False
    
    def test_delete_book(self):
        """Prueba eliminar un libro"""
        self.log("=== Probando Eliminar Libro ===")
        delete_data = {
            "isbn": "978-84-376-9999-9"
        }
        
        response = self.make_request("DELETE", "/api/books/delete", data=delete_data, expected_status=200)
        
        if response:
            data = response.json()
            self.log(f"Libro eliminado: {data}")
            return True
        return False
    
    def test_refresh_token(self):
        """Prueba el refresh de token"""
        if not self.refresh_token:
            self.log('error', 'No hay refresh token disponible')
            return False
            
        self.log("=== Probando Refresh Token ===")
        # Usar refresh token en lugar de access token
        headers = {"Authorization": f"Bearer {self.refresh_token}"}
        response = self.make_request("POST", "/auth/refresh", headers=headers, expected_status=200)
        
        if response:
            data = response.json()
            old_token = self.access_token
            self.access_token = data["access_token"]
            self.log(f"Token refrescado exitosamente")
            self.log(f"Token anterior: {old_token[:20]}...")
            self.log(f"Token nuevo: {self.access_token[:20]}...")
            return True
        return False
    
    def test_unauthorized_access(self):
        """Prueba acceso sin token"""
        self.log("=== Probando Acceso No Autorizado ===")
        # Guardar token temporalmente
        temp_token = self.access_token
        self.access_token = None
        
        response = self.make_request("GET", "/api/books", expected_status=401)
        
        # Restaurar token
        self.access_token = temp_token
        
        if response:
            self.log("Acceso no autorizado correctamente bloqueado")
            return True
        return False
    
    def test_invalid_token(self):
        """Prueba con token inválido"""
        self.log("=== Probando Token Inválido ===")
        # Guardar token temporalmente
        temp_token = self.access_token
        self.access_token = "invalid_token_here"
        
        response = self.make_request("GET", "/api/books", expected_status=422)
        
        # Restaurar token
        self.access_token = temp_token
        
        if response:
            self.log("Token inválido correctamente rechazado")
            return True
        return False
    
    def test_logout(self):
        """Prueba el logout"""
        self.log("=== Probando Logout ===")
        response = self.make_request("POST", "/auth/logout", expected_status=200)
        
        if response:
            data = response.json()
            self.log(f"Logout exitoso: {data}")
            return True
        return False
    
    def run_all_tests(self):
        """Ejecuta todas las pruebas"""
        self.log("🚀 Iniciando pruebas del microservicio de Libros con JWT + Redis")
        self.log("=" * 60)
        
        tests = [
            ("Health Check", self.test_health),
            ("Registro", self.test_register),
            ("Login", self.test_login),
            ("Estado de Autenticación", self.test_auth_status),
            ("Obtener Todos los Libros", self.test_get_all_books),
            ("Obtener Libro por ISBN", self.test_get_book_by_isbn),
            ("Obtener Libros Digitales", self.test_get_digital_books),
            ("Obtener Libros por Autor", self.test_get_books_by_author),
            ("Crear Libro", self.test_create_book),
            ("Actualizar Libro", self.test_update_book),
            ("Eliminar Libro", self.test_delete_book),
            ("Refresh Token", self.test_refresh_token),
            ("Acceso No Autorizado", self.test_unauthorized_access),
            ("Token Inválido", self.test_invalid_token),
            ("Logout", self.test_logout),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                self.log(f"\n--- {test_name} ---")
                if test_func():
                    passed += 1
                    self.log(f"✅ {test_name}: PASÓ", "SUCCESS")
                else:
                    failed += 1
                    self.log(f"❌ {test_name}: FALLÓ", "ERROR")
            except Exception as e:
                failed += 1
                self.log(f"❌ {test_name}: ERROR - {e}", "ERROR")
            
            time.sleep(0.5)  # Pausa entre pruebas
        
        self.log("\n" + "=" * 60)
        self.log(f"📊 RESUMEN DE PRUEBAS:")
        self.log(f"✅ Pasaron: {passed}")
        self.log(f"❌ Fallaron: {failed}")
        self.log(f"📈 Total: {passed + failed}")
        self.log(f"🎯 Tasa de éxito: {(passed / (passed + failed) * 100):.1f}%")
        
        if failed == 0:
            self.log("🎉 ¡Todas las pruebas pasaron exitosamente!", "SUCCESS")
        else:
            self.log(f"⚠️  {failed} pruebas fallaron. Revisar logs.", "WARNING")

if __name__ == "__main__":
    tester = BooksAPITester(BASE_URL)
    tester.run_all_tests()
