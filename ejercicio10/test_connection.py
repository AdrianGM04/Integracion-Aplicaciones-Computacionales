#!/usr/bin/env python3
"""
Script de diagnóstico para verificar la conectividad con el microservicio
Ejercicio 10 - Integración de Aplicaciones Computacionales
"""

import requests
import json
import sys
from datetime import datetime

# Configuración
HOST = "http://136.112.218.8:5000"
TIMEOUT = 10

def print_header(text):
    """Imprime un encabezado formateado"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_success(text):
    """Imprime un mensaje de éxito"""
    print(f"✅ {text}")

def print_error(text):
    """Imprime un mensaje de error"""
    print(f"❌ {text}")

def print_warning(text):
    """Imprime un mensaje de advertencia"""
    print(f"⚠️  {text}")

def test_health(host=HOST):
    """Prueba el endpoint /health"""
    print_header("1. Probando endpoint /health")
    try:
        response = requests.get(f"{host}/health", timeout=TIMEOUT)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print_success("Conexión exitosa")
                print(f"Respuesta: {json.dumps(data, indent=2)}")
                return True
            except json.JSONDecodeError:
                print_warning("Respuesta no es JSON válido")
                print(f"Respuesta: {response.text[:200]}")
                return False
        else:
            print_error(f"Status code inesperado: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("No se puede conectar al servidor")
        print(f"   Verifica que el microservicio esté corriendo en {host}")
        return False
    except requests.exceptions.Timeout:
        print_error(f"Timeout después de {TIMEOUT} segundos")
        return False
    except Exception as e:
        print_error(f"Error inesperado: {str(e)}")
        return False

def test_register(host=HOST):
    """Prueba el endpoint /register"""
    print_header("2. Probando endpoint /register")
    import random
    import string
    
    username = f"testuser_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"
    email = f"{username}@test.com"
    password = "TestPassword123!"
    
    payload = {
        "username": username,
        "email": email,
        "password": password
    }
    
    print(f"Registrando usuario: {username}")
    try:
        response = requests.post(
            f"{host}/register",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            print_success("Usuario registrado exitosamente")
            try:
                data = response.json()
                print(f"Respuesta: {json.dumps(data, indent=2)}")
                return True, username, password
            except:
                return True, username, password
        elif response.status_code == 409:
            print_warning("Usuario ya existe (esto es normal si ya se registró antes)")
            return True, username, password
        else:
            print_error(f"Error al registrar: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")
            return False, None, None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, None, None

def test_login(username, password, host=HOST):
    """Prueba el endpoint /login"""
    print_header("3. Probando endpoint /login")
    
    if not username or not password:
        print_warning("Saltando login (no hay credenciales válidas)")
        return None, None, None
    
    payload = {
        "username": username,
        "password": password
    }
    
    print(f"Intentando login con usuario: {username}")
    try:
        response = requests.post(
            f"{host}/login",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                access_token = data.get("access_token")
                refresh_token = data.get("refresh_token")
                session_id = data.get("session_id")
                
                if access_token and refresh_token:
                    print_success("Login exitoso")
                    print(f"Session ID: {session_id}")
                    print(f"Access Token: {access_token[:50]}...")
                    print(f"Refresh Token: {refresh_token[:50]}...")
                    return access_token, refresh_token, session_id
                else:
                    print_error("Tokens no recibidos en la respuesta")
                    print(f"Respuesta: {json.dumps(data, indent=2)}")
                    return None, None, None
            except json.JSONDecodeError:
                print_error("Respuesta no es JSON válido")
                print(f"Respuesta: {response.text[:200]}")
                return None, None, None
        elif response.status_code == 401:
            print_error("Credenciales inválidas")
            print("   Intenta crear un usuario primero o verifica las credenciales")
            return None, None, None
        else:
            print_error(f"Error en login: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")
            return None, None, None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None, None, None

def test_protected(access_token, host=HOST):
    """Prueba el endpoint /protected"""
    print_header("4. Probando endpoint /protected")
    
    if not access_token:
        print_warning("Saltando /protected (no hay access token)")
        return False
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(
            f"{host}/protected",
            headers=headers,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print_success("Acceso a endpoint protegido exitoso")
            try:
                data = response.json()
                print(f"Respuesta: {json.dumps(data, indent=2)}")
                return True
            except:
                return True
        elif response.status_code == 401:
            print_error("Token inválido o expirado")
            return False
        else:
            print_error(f"Error: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_refresh(refresh_token, host=HOST):
    """Prueba el endpoint /refresh"""
    print_header("5. Probando endpoint /refresh")
    
    if not refresh_token:
        print_warning("Saltando /refresh (no hay refresh token)")
        return None
    
    headers = {
        "Authorization": f"Bearer {refresh_token}"
    }
    
    try:
        response = requests.post(
            f"{host}/refresh",
            headers=headers,
            timeout=TIMEOUT
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                new_access_token = data.get("access_token")
                if new_access_token:
                    print_success("Refresh token exitoso")
                    print(f"New Access Token: {new_access_token[:50]}...")
                    return new_access_token
                else:
                    print_error("Nuevo access token no recibido")
                    return None
            except:
                return None
        else:
            print_error(f"Error: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")
            return None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None

def main():
    """Función principal"""
    # Verificar si se puede cambiar el host desde argumentos
    host = HOST
    if len(sys.argv) > 1:
        host = sys.argv[1]
    
    print_header("DIAGNÓSTICO DE CONECTIVIDAD DEL MICROSERVICIO")
    print(f"Host: {host}")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        "health": False,
        "register": False,
        "login": False,
        "protected": False,
        "refresh": False
    }
    
    # 1. Health check
    results["health"] = test_health(host)
    
    if not results["health"]:
        print("\n" + "="*60)
        print_error("No se pudo conectar al servidor. Verifica:")
        print("   1. Que el microservicio esté corriendo")
        print("   2. Que la URL sea correcta")
        print("   3. Que no haya problemas de firewall/red")
        print("="*60)
        sys.exit(1)
    
    # 2. Register
    register_ok, username, password = test_register(host)
    results["register"] = register_ok
    
    # 3. Login
    access_token, refresh_token, session_id = test_login(username, password, host)
    results["login"] = access_token is not None
    
    # 4. Protected
    if access_token:
        results["protected"] = test_protected(access_token, host)
    
    # 5. Refresh
    if refresh_token:
        new_token = test_refresh(refresh_token, host)
        results["refresh"] = new_token is not None
    
    # Resumen
    print_header("RESUMEN DE PRUEBAS")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name.upper()}")
    
    all_passed = all(results.values())
    print("\n" + "="*60)
    if all_passed:
        print_success("TODAS LAS PRUEBAS PASARON")
        print("El microservicio está funcionando correctamente.")
        print("Puedes ejecutar Locust sin problemas.")
    else:
        print_error("ALGUNAS PRUEBAS FALLARON")
        print("Revisa los errores arriba antes de ejecutar Locust.")
    print("="*60 + "\n")
    
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()

