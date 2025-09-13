@echo off
REM Script de inicio para el chatbot Ollama + Flask (Windows)
REM Este script automatiza el proceso de despliegue

echo 🚀 Iniciando Chatbot con Ollama y Flask
echo ========================================

REM Verificar si Docker está instalado
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker no está instalado. Por favor instala Docker Desktop primero.
    pause
    exit /b 1
)

REM Verificar si Docker Compose está instalado
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose no está instalado. Por favor instala Docker Compose primero.
    pause
    exit /b 1
)

echo ✅ Docker y Docker Compose están disponibles

REM Detener contenedores existentes si los hay
echo 🛑 Deteniendo contenedores existentes...
docker-compose down 2>nul

REM Construir y ejecutar los servicios
echo 🔨 Construyendo y ejecutando servicios...
docker-compose up -d --build

REM Esperar a que Ollama esté listo
echo ⏳ Esperando a que Ollama esté listo...
timeout /t 10 /nobreak >nul

REM Verificar que Ollama esté funcionando
echo 🔍 Verificando estado de Ollama...
set /a max_attempts=30
set /a attempt=1

:check_ollama
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Ollama está funcionando correctamente
    goto :download_model
) else (
    echo ⏳ Intento %attempt%/%max_attempts% - Esperando Ollama...
    timeout /t 2 /nobreak >nul
    set /a attempt+=1
    if %attempt% leq %max_attempts% goto :check_ollama
)

echo ❌ Ollama no respondió después de %max_attempts% intentos
echo 📋 Revisa los logs: docker logs ollama
pause
exit /b 1

:download_model
REM Descargar el modelo DeepSeek Coder
echo 📥 Descargando modelo DeepSeek Coder...
docker exec -it ollama ollama pull deepseek-coder

if %errorlevel% equ 0 (
    echo ✅ Modelo DeepSeek Coder descargado exitosamente
) else (
    echo ❌ Error al descargar el modelo
    echo 📋 Puedes intentar manualmente: docker exec -it ollama ollama pull deepseek-coder
)

REM Verificar que la aplicación Flask esté funcionando
echo 🔍 Verificando aplicación Flask...
timeout /t 5 /nobreak >nul

curl -s http://localhost:5000/api/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Aplicación Flask está funcionando correctamente
) else (
    echo ⚠️  La aplicación Flask puede no estar lista aún
)

echo.
echo 🎉 ¡Despliegue completado!
echo ==========================
echo 🌐 Aplicación web: http://localhost:5000
echo 🤖 API Ollama: http://localhost:11434
echo.
echo 📋 Comandos útiles:
echo    Ver logs: docker-compose logs -f
echo    Detener: docker-compose down
echo    Reiniciar: docker-compose restart
echo.
echo 🔧 Para cambiar el modelo:
echo    docker exec -it ollama ollama pull llama3
echo    docker exec -it ollama ollama pull codellama
echo.
echo ¡Disfruta tu chatbot! 🤖✨
pause
