# Ejercicio 7: Comparación Redis vs MariaDB

## 📋 Descripción
Este programa compara el rendimiento entre Redis y MariaDB utilizando la tabla `JWT03.users`. Demuestra por qué Redis es significativamente más rápido que MariaDB para operaciones de lectura y escritura.

## 🚀 Características
- **Comparación de rendimiento**: Mide tiempos de inserción y lectura en ambas bases de datos
- **Análisis estadístico**: Ejecuta múltiples iteraciones para obtener métricas precisas
- **Interfaz interactiva**: Menú con opciones para registro, consulta y pruebas completas
- **Explicación técnica**: Análisis detallado de por qué Redis es más rápido

## 📦 Instalación

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar variables de entorno:**
   - Copia `config.env` y modifica los valores según tu configuración
   - Para pruebas en la nube, actualiza los hosts y credenciales

3. **Asegurar que las bases de datos estén ejecutándose:**
   - Redis en el puerto 6379
   - MariaDB en el puerto 3306 con la base de datos JWT03

## 🎯 Uso

```bash
python app.py
```

### Opciones disponibles:
1. **Registro de nuevo usuario**: Crea un usuario y compara tiempos de escritura/lectura
2. **Consulta de usuario existente**: Busca un usuario y compara tiempos de consulta
3. **Prueba de rendimiento completa**: Ejecuta múltiples iteraciones para análisis estadístico

## 📊 Resultados esperados
- Redis típicamente es **10-100x más rápido** que MariaDB
- Los tiempos de Redis están en **microsegundos**
- Los tiempos de MariaDB están en **milisegundos**

## 🔧 Configuración

### Variables de entorno (config.env):
```env
# REDIS
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# MARIADB / MYSQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=JWT03
MYSQL_USER=libros_user
MYSQL_PASSWORD=666
```

### Para pruebas en la nube:
- Cambia `localhost` por las IPs/hosts de tus servidores
- Actualiza las credenciales según tu configuración
- Asegúrate de que los puertos estén abiertos

## 🏗️ Arquitectura
- **Redis**: Almacenamiento en memoria (RAM) con operaciones directas
- **MariaDB**: Almacenamiento en disco con cache en memoria y procesamiento SQL

## 📈 Casos de uso
- **Redis**: Ideal para cache, sesiones, contadores, colas
- **MariaDB**: Ideal para datos transaccionales, reportes, análisis complejos
