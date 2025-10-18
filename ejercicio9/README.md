# 🚀 Microservicio GUI - Consumidor de Endpoints

Aplicación Java con interfaz gráfica para consumir endpoints de un microservicio.

## 📋 Requisitos

- **Java 17** o superior
- **Maven 3.6+**

## 🛠️ Instalación y Configuración

### 1. Instalar Java 17
```bash
# Windows (usando winget)
winget install Microsoft.OpenJDK.17

# Configurar variables de entorno
$env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-17.0.16.8-hotspot"
$env:PATH = "C:\Program Files\Microsoft\jdk-17.0.16.8-hotspot\bin;" + $env:PATH
```

### 2. Compilar el proyecto
```bash
mvn clean compile
```

### 3. Crear JAR ejecutable
```bash
mvn package
```

## 🎯 Ejecución

### Ejecutar la aplicación
```bash
java -jar target/microservice-gui-1.0.0.jar
```

## 🔧 Funcionalidades

- **Monitoreo de salud** del microservicio
- **Autenticación** (registro, login, logout)
- **Gestión de tokens** (renovación automática)
- **Acceso a endpoints protegidos**
- **Interfaz gráfica** intuitiva
- **Configuración** de URL del microservicio

## 📁 Estructura del Proyecto

```
ejercicio9/
├── src/main/java/com/microservice/gui/
│   ├── components/          # Componentes de la GUI
│   ├── config/             # Gestión de configuración
│   ├── services/           # Clientes y monitoreo
│   ├── MicroserviceGUI.java # Aplicación principal
│   └── MicroserviceCLI.java # Versión CLI
├── target/
│   └── microservice-gui-1.0.0.jar # JAR ejecutable
├── pom.xml                 # Configuración Maven
├── microservice_config.json # Configuración del servicio
└── README.md              # Este archivo
```

## 🌐 Configuración

La aplicación se conecta por defecto a `http://127.0.0.1:5000`. Puedes cambiar la URL del microservicio desde la interfaz gráfica.

## 📝 Logs

Los logs se muestran en tiempo real en la interfaz gráfica y también se guardan en archivos de log.

## 🔄 Endpoints Soportados

- `GET /health` - Estado del servicio
- `POST /register` - Registro de usuario
- `POST /login` - Autenticación
- `POST /refresh` - Renovación de tokens
- `GET /protected` - Endpoint protegido
- `POST /logout` - Cierre de sesión

---

**Nota**: Esta aplicación está diseñada para funcionar con un microservicio compatible con los endpoints mencionados.