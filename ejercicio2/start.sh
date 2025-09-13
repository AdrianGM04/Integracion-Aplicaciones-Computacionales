#!/bin/bash

# Script de inicio para el chatbot Ollama + Flask
# Este script automatiza el proceso de despliegue

echo "🚀 Iniciando Chatbot con Ollama y Flask"
echo "========================================"

# Verificar si Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado. Por favor instala Docker primero."
    exit 1
fi

# Verificar si Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado. Por favor instala Docker Compose primero."
    exit 1
fi

echo "✅ Docker y Docker Compose están disponibles"

# Detener contenedores existentes si los hay
echo "🛑 Deteniendo contenedores existentes..."
docker-compose down 2>/dev/null || true

# Construir y ejecutar los servicios
echo "🔨 Construyendo y ejecutando servicios..."
docker-compose up -d --build

# Esperar a que Ollama esté listo
echo "⏳ Esperando a que Ollama esté listo..."
sleep 10

# Verificar que Ollama esté funcionando
echo "🔍 Verificando estado de Ollama..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama está funcionando correctamente"
        break
    else
        echo "⏳ Intento $attempt/$max_attempts - Esperando Ollama..."
        sleep 2
        ((attempt++))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Ollama no respondió después de $max_attempts intentos"
    echo "📋 Revisa los logs: docker logs ollama"
    exit 1
fi

# Descargar el modelo DeepSeek Coder
echo "📥 Descargando modelo DeepSeek Coder..."
docker exec -it ollama ollama pull deepseek-coder

if [ $? -eq 0 ]; then
    echo "✅ Modelo DeepSeek Coder descargado exitosamente"
else
    echo "❌ Error al descargar el modelo"
    echo "📋 Puedes intentar manualmente: docker exec -it ollama ollama pull deepseek-coder"
fi

# Verificar que la aplicación Flask esté funcionando
echo "🔍 Verificando aplicación Flask..."
sleep 5

if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "✅ Aplicación Flask está funcionando correctamente"
else
    echo "⚠️  La aplicación Flask puede no estar lista aún"
fi

echo ""
echo "🎉 ¡Despliegue completado!"
echo "=========================="
echo "🌐 Aplicación web: http://localhost:5000"
echo "🤖 API Ollama: http://localhost:11434"
echo ""
echo "📋 Comandos útiles:"
echo "   Ver logs: docker-compose logs -f"
echo "   Detener: docker-compose down"
echo "   Reiniciar: docker-compose restart"
echo ""
echo "🔧 Para cambiar el modelo:"
echo "   docker exec -it ollama ollama pull llama3"
echo "   docker exec -it ollama ollama pull codellama"
echo ""
echo "¡Disfruta tu chatbot! 🤖✨"
