#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Análisis de Rendimiento: Redis vs MariaDB
Sistema de Benchmark para Base de Datos JWT03.users

Características:
- Comparación directa de velocidad entre Redis y MariaDB
- Operaciones de escritura y lectura con métricas precisas
- Análisis estadístico de rendimiento
- Explicación técnica de las diferencias de velocidad
"""

import os
import time
import statistics
from typing import Tuple, Optional, Dict, List
import redis
import pymysql
from dotenv import load_dotenv

# Configuración de conexiones
load_dotenv('config.env')

# Parámetros de conexión
REDIS_CONFIG = {
    'host': os.getenv("REDIS_HOST", "127.0.0.1"),
    'port': int(os.getenv("REDIS_PORT", "6379")),
    'db': int(os.getenv("REDIS_DB", "0")),
    'decode_responses': True
}

MYSQL_CONFIG = {
    'host': os.getenv("MYSQL_HOST", "127.0.0.1"),
    'port': int(os.getenv("MYSQL_PORT", "3306")),
    'user': os.getenv("MYSQL_USER", "libros_user"),
    'password': os.getenv("MYSQL_PASSWORD", "666"),
    'database': os.getenv("MYSQL_DB", "JWT03"),
    'autocommit': True,
    'charset': "utf8mb4",
    'cursorclass': pymysql.cursors.DictCursor
}

class DatabaseBenchmark:
    """Clase para realizar comparaciones de rendimiento entre Redis y MariaDB"""
    
    def __init__(self):
        self.redis_client = None
        self.mysql_connection = None
    
    def connect_redis(self) -> redis.Redis:
        """Establece conexión con Redis"""
        if not self.redis_client:
            self.redis_client = redis.Redis(**REDIS_CONFIG)
        return self.redis_client
    
    def connect_mysql(self) -> pymysql.Connection:
        """Establece conexión con MariaDB"""
        if not self.mysql_connection:
            self.mysql_connection = pymysql.connect(**MYSQL_CONFIG)
        return self.mysql_connection
    
    def generate_user_key(self, username: str) -> str:
        """Genera clave única para usuario en Redis"""
        return f"benchmark:user:{username}"
    
    def store_in_redis(self, username: str, email: str, password: str) -> float:
        """Almacena datos de usuario en Redis y retorna tiempo de ejecución"""
        redis_client = self.connect_redis()
        user_key = self.generate_user_key(username)
        
        start_time = time.perf_counter()
        redis_client.hset(user_key, mapping={
            "username": username,
            "email": email,
            "password": password,
            "created_at": str(int(time.time()))
        })
        end_time = time.perf_counter()
        
        return end_time - start_time
    
    def retrieve_from_redis(self, username: str) -> Tuple[Optional[Dict], float]:
        """Recupera datos de usuario desde Redis y retorna tiempo de ejecución"""
        redis_client = self.connect_redis()
        user_key = self.generate_user_key(username)
        
        start_time = time.perf_counter()
        user_data = redis_client.hgetall(user_key)
        end_time = time.perf_counter()
        
        execution_time = end_time - start_time
        return (user_data if user_data else None, execution_time)
    
    def store_in_mysql(self, username: str, email: str, password: str) -> float:
        """Almacena datos de usuario en MariaDB y retorna tiempo de ejecución"""
        connection = self.connect_mysql()
        
        start_time = time.perf_counter()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                    (username, email, password)
                )
        except pymysql.err.IntegrityError:
            print("⚠️  El usuario ya existe en MariaDB")
            return 0.0
        finally:
            end_time = time.perf_counter()
        
        return end_time - start_time
    
    def retrieve_from_mysql(self, username: str) -> Tuple[Optional[Dict], float]:
        """Recupera datos de usuario desde MariaDB y retorna tiempo de ejecución"""
        connection = self.connect_mysql()
        
        start_time = time.perf_counter()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT username, email, password_hash FROM users WHERE username = %s",
                    (username,)
                )
                result = cursor.fetchone()
        finally:
            end_time = time.perf_counter()
        
        execution_time = end_time - start_time
        return (result, execution_time)
    
    def calculate_performance_ratio(self, mysql_time: float, redis_time: float) -> str:
        """Calcula cuántas veces es más lento MariaDB comparado con Redis"""
        if redis_time <= 1e-9:
            return "No aplicable"
        ratio = mysql_time / redis_time
        return f"{ratio:.2f}x más lento"
    
    def run_performance_test(self, username: str, email: str, password: str, iterations: int = 5) -> Dict:
        """Ejecuta múltiples iteraciones para obtener métricas estadísticas"""
        redis_write_times = []
        mysql_write_times = []
        redis_read_times = []
        mysql_read_times = []
        
        print(f"🔄 Ejecutando {iterations} iteraciones de prueba...")
        
        for i in range(iterations):
            # Pruebas de escritura
            redis_time = self.store_in_redis(username, email, password)
            mysql_time = self.store_in_mysql(username, email, password)
            
            if redis_time > 0:
                redis_write_times.append(redis_time)
            if mysql_time > 0:
                mysql_write_times.append(mysql_time)
            
            # Pruebas de lectura
            _, redis_read_time = self.retrieve_from_redis(username)
            _, mysql_read_time = self.retrieve_from_mysql(username)
            
            redis_read_times.append(redis_read_time)
            mysql_read_times.append(mysql_read_time)
        
        return {
            'redis_write': redis_write_times,
            'mysql_write': mysql_write_times,
            'redis_read': redis_read_times,
            'mysql_read': mysql_read_times
        }
    
    def display_results(self, results: Dict, username: str):
        """Muestra resultados detallados del benchmark"""
        print("\n" + "="*60)
        print("📊 RESULTADOS DEL ANÁLISIS DE RENDIMIENTO")
        print("="*60)
        
        # Estadísticas de escritura
        if results['redis_write'] and results['mysql_write']:
            redis_avg_write = statistics.mean(results['redis_write'])
            mysql_avg_write = statistics.mean(results['mysql_write'])
            
            print(f"\n📝 OPERACIONES DE ESCRITURA:")
            print(f"   Redis promedio:   {redis_avg_write*1000:.3f} ms")
            print(f"   MariaDB promedio: {mysql_avg_write*1000:.3f} ms")
            print(f"   MariaDB es {self.calculate_performance_ratio(mysql_avg_write, redis_avg_write)} en escritura")
        
        # Estadísticas de lectura
        redis_avg_read = statistics.mean(results['redis_read'])
        mysql_avg_read = statistics.mean(results['mysql_read'])
        
        print(f"\n📖 OPERACIONES DE LECTURA:")
        print(f"   Redis promedio:   {redis_avg_read*1000:.3f} ms")
        print(f"   MariaDB promedio: {mysql_avg_read*1000:.3f} ms")
        print(f"   MariaDB es {self.calculate_performance_ratio(mysql_avg_read, redis_avg_read)} en lectura")
        
        # Verificación de datos
        redis_data, _ = self.retrieve_from_redis(username)
        mysql_data, _ = self.retrieve_from_mysql(username)
        
        print(f"\n🔍 VERIFICACIÓN DE DATOS:")
        print(f"   Datos en Redis:   {redis_data}")
        print(f"   Datos en MariaDB: {mysql_data}")
        
        # Análisis técnico
        self.display_technical_analysis()
    
    def display_technical_analysis(self):
        """Muestra análisis técnico de por qué Redis es más rápido"""
        print(f"\n" + "="*60)
        print("🔬 ANÁLISIS TÉCNICO: ¿Por qué Redis es más rápido?")
        print("="*60)
        print("""
💾 ARQUITECTURA DE ALMACENAMIENTO:
   • Redis: Almacenamiento completamente en memoria (RAM)
   • MariaDB: Almacenamiento en disco con cache en memoria

⚡ VELOCIDAD DE ACCESO:
   • Redis: Acceso directo a memoria (nanosegundos)
   • MariaDB: Acceso a disco + procesamiento SQL (milisegundos)

🏗️ COMPLEJIDAD DE OPERACIONES:
   • Redis: Operaciones simples y directas (HSET, HGET)
   • MariaDB: Parser SQL + optimizador + motor de transacciones

🔄 PERSISTENCIA Y CONFIABILIDAD:
   • Redis: Velocidad optimizada, persistencia opcional
   • MariaDB: ACID completo, transacciones, integridad garantizada

📈 CASOS DE USO IDEALES:
   • Redis: Cache, sesiones, contadores, colas
   • MariaDB: Datos transaccionales, reportes, análisis complejos
        """)

def main():
    """Función principal del programa"""
    print("🚀 BENCHMARK: REDIS vs MARIADB")
    print("Base de datos: JWT03.users")
    print("-" * 40)
    
    # Entrada de datos del usuario
    username = input("👤 Ingresa tu nombre de usuario: ").strip()
    password = input("🔐 Ingresa tu contraseña: ").strip()
    
    print("\n¿Qué operación deseas realizar?")
    print("1. Registro de nuevo usuario")
    print("2. Consulta de usuario existente")
    print("3. Prueba de rendimiento completa")
    
    choice = input("Selecciona una opción (1-3): ").strip()
    
    benchmark = DatabaseBenchmark()
    
    if choice == "1":
        # Registro de usuario
        email = input("📧 Ingresa tu email: ").strip()
        
        print("\n⏱️  Ejecutando operaciones...")
        
        # Escritura
        redis_write_time = benchmark.store_in_redis(username, email, password)
        mysql_write_time = benchmark.store_in_mysql(username, email, password)
        
        print(f"\n📝 TIEMPOS DE ESCRITURA:")
        print(f"   Redis:   {redis_write_time*1000:.3f} ms")
        print(f"   MariaDB: {mysql_write_time*1000:.3f} ms")
        print(f"   MariaDB es {benchmark.calculate_performance_ratio(mysql_write_time, redis_write_time)} en escritura")
        
        # Lectura inmediata
        redis_data, redis_read_time = benchmark.retrieve_from_redis(username)
        mysql_data, mysql_read_time = benchmark.retrieve_from_mysql(username)
        
        print(f"\n📖 TIEMPOS DE LECTURA:")
        print(f"   Redis:   {redis_read_time*1000:.3f} ms")
        print(f"   MariaDB: {mysql_read_time*1000:.3f} ms")
        print(f"   MariaDB es {benchmark.calculate_performance_ratio(mysql_read_time, redis_read_time)} en lectura")
        
        print(f"\n✅ Usuario registrado exitosamente!")
        
    elif choice == "2":
        # Consulta de usuario
        print("\n🔍 Consultando usuario...")
        
        redis_data, redis_time = benchmark.retrieve_from_redis(username)
        mysql_data, mysql_time = benchmark.retrieve_from_mysql(username)
        
        print(f"\n📖 TIEMPOS DE CONSULTA:")
        print(f"   Redis:   {redis_time*1000:.3f} ms")
        print(f"   MariaDB: {mysql_time*1000:.3f} ms")
        print(f"   MariaDB es {benchmark.calculate_performance_ratio(mysql_time, redis_time)} en consulta")
        
        if redis_data and mysql_data:
            if redis_data.get("password") == password and mysql_data.get("password_hash") == password:
                print("✅ Inicio de sesión exitoso")
            else:
                print("❌ Contraseña incorrecta")
        else:
            print("❌ Usuario no encontrado")
            
    elif choice == "3":
        # Prueba completa de rendimiento
        email = input("📧 Ingresa tu email: ").strip()
        iterations = int(input("🔄 Número de iteraciones (recomendado: 5): ") or "5")
        
        results = benchmark.run_performance_test(username, email, password, iterations)
        benchmark.display_results(results, username)
    
    else:
        print("❌ Opción no válida")

if __name__ == "__main__":
    main()
