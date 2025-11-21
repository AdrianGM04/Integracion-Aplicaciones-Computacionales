#!/bin/bash
# Script de inicio para la aplicación Flask en GCP

# Cambiar al directorio del script
cd "$(dirname "$0")"

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "[*] Activando entorno virtual..."
    source venv/bin/activate
else
    echo "[ERROR] No se encontró el entorno virtual 'venv'"
    echo "Ejecuta primero: ./setup_gcp.sh"
    exit 1
fi

# Verificar que las dependencias estén instaladas
if ! python3 -c "import flask_swagger_ui" 2>/dev/null; then
    echo "[*] Instalando dependencias faltantes..."
    pip install -r requirements.txt
fi

# Cargar variables de entorno
if [ -f "config.env" ]; then
    echo "[*] Cargando configuración desde config.env..."
    export $(cat config.env | grep -v '^#' | xargs)
else
    echo "[WARN] No se encontró config.env, usando valores por defecto"
fi

# Ejecutar la aplicación
echo "[*] Iniciando aplicación Flask..."
python3 app2.py

