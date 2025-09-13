# Chatbot con Ollama y Flask

Este proyecto implementa un chatbot web que utiliza Ollama para ejecutar modelos de lenguaje localmente, específicamente DeepSeek Coder.

## 🚀 Características

- **Interfaz web moderna y responsive** con diseño atractivo
- **Integración con Ollama** para ejecutar modelos LLM localmente
- **Soporte para CORS** para evitar problemas de cross-origin
- **Manejo de errores robusto** con mensajes informativos
- **Indicador de estado** en tiempo real
- **Dockerizado** para fácil despliegue

## 📋 Requisitos

- Docker y Docker Compose
- Al menos 4GB de RAM disponible para Ollama
- Puerto 5000 y 11434 disponibles

## 🛠️ Instalación y Uso

### Opción 1: Usando Docker Compose (Recomendado)

1. **Clonar o descargar el proyecto**
2. **Ejecutar el stack completo:**
   ```bash
   docker-compose up -d
   ```

3. **Descargar el modelo DeepSeek Coder:**
   ```bash
   docker exec -it ollama ollama pull deepseek-coder
   ```

4. **Acceder a la aplicación:**
   - Abrir navegador en `http://localhost:5000`

### Opción 2: Ejecución Manual

1. **Ejecutar Ollama:**
   ```bash
   docker run -d -p 11434:11434 --name ollama ollama/ollama
   ```

2. **Descargar el modelo:**
   ```bash
   docker exec -it ollama ollama pull deepseek-coder
   ```

3. **Ejecutar la aplicación Flask:**
   ```bash
   # Instalar dependencias
   pip install -r requirements.txt
   
   # Ejecutar aplicación
   python app.py
   ```

4. **Acceder a la aplicación:**
   - Abrir navegador en `http://localhost:5000`

## 🔧 Configuración

### Variables de Entorno

- `OLLAMA_URL`: URL del servidor Ollama (default: `http://localhost:11434`)
- `MODEL_NAME`: Nombre del modelo a usar (default: `deepseek-coder`)

### Modelos Disponibles

Puedes cambiar el modelo modificando la variable `MODEL_NAME` o descargando otros modelos:

```bash
# Descargar otros modelos
docker exec -it ollama ollama pull llama3
docker exec -it ollama ollama pull codellama
docker exec -it ollama ollama pull mistral
```

## 📁 Estructura del Proyecto

```
.
├── app.py                 # Aplicación Flask principal
├── templates/
│   └── index.html        # Interfaz web del chatbot
├── requirements.txt      # Dependencias de Python
├── Dockerfile           # Imagen Docker para Flask
├── docker-compose.yml   # Orquestación de servicios
└── README.md           # Este archivo
```

## 🔍 API Endpoints

### `GET /`
Página principal con la interfaz del chatbot.

### `POST /api/chat`
Enviar mensaje al chatbot.

**Request:**
```json
{
  "message": "¿Qué es Python?"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Python es un lenguaje de programación...",
  "model": "deepseek-coder"
}
```

### `GET /api/health`
Verificar estado de Ollama.

**Response:**
```json
{
  "status": "healthy",
  "ollama_url": "http://localhost:11434",
  "available_models": ["deepseek-coder", "llama3"]
}
```

## 🐛 Solución de Problemas

### Error de Conexión con Ollama
- Verificar que el contenedor de Ollama esté ejecutándose: `docker ps`
- Verificar que el puerto 11434 esté disponible
- Revisar logs: `docker logs ollama`

### Modelo No Encontrado
- Verificar que el modelo esté descargado: `docker exec -it ollama ollama list`
- Descargar el modelo: `docker exec -it ollama ollama pull deepseek-coder`

### Problemas de CORS
- La aplicación ya incluye Flask-CORS para manejar estos problemas
- Si persisten, verificar configuración de red entre contenedores

### Memoria Insuficiente
- Ollama requiere al menos 4GB de RAM
- Considerar usar modelos más pequeños si hay limitaciones de memoria

## 🛑 Detener la Aplicación

```bash
# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v
```

## 📝 Notas Adicionales

- La primera ejecución puede tardar varios minutos mientras se descarga el modelo
- Los modelos se almacenan en un volumen persistente para evitar re-descargas
- La aplicación está optimizada para desarrollo y producción
- Incluye manejo de errores robusto y logging

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request para sugerir mejoras.
