#!/bin/bash

# Script para ejecutar pruebas de rendimiento con Locust
# Ejercicio 10 - Integración de Aplicaciones Computacionales

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuración por defecto
HOST="${LOCUST_HOST:-http://136.112.218.8:5000}"
USERS="${LOCUST_USERS:-10}"
SPAWN_RATE="${LOCUST_SPAWN_RATE:-2}"
RUN_TIME="${LOCUST_RUN_TIME:-}"
MODE="${LOCUST_MODE:-interactive}"

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [OPCIONES]"
    echo ""
    echo "Opciones:"
    echo "  -h, --help              Mostrar esta ayuda"
    echo "  -m, --mode MODE         Modo de ejecución: interactive, quick, load, stress (default: interactive)"
    echo "  -u, --users NUM         Número de usuarios simultáneos (default: 10)"
    echo "  -r, --spawn-rate NUM    Usuarios por segundo (default: 2)"
    echo "  -t, --time TIME         Tiempo de ejecución (ej: 5m, 1h) (solo para modo headless)"
    echo "  --host HOST             Host del microservicio (default: http://136.112.218.8:5000)"
    echo ""
    echo "Modos predefinidos:"
    echo "  interactive             Modo interactivo con interfaz web (default)"
    echo "  quick                   Prueba rápida: 5 usuarios, 1 minuto"
    echo "  load                    Prueba de carga: 50 usuarios, 10 minutos"
    echo "  stress                  Prueba de estrés: 100 usuarios, 30 minutos"
    echo ""
    echo "Ejemplos:"
    echo "  $0                                    # Modo interactivo"
    echo "  $0 -m quick                           # Prueba rápida"
    echo "  $0 -m load -u 100 -r 10               # Prueba personalizada"
    echo "  $0 --host http://localhost:5000       # Cambiar host"
}

# Parsear argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -u|--users)
            USERS="$2"
            shift 2
            ;;
        -r|--spawn-rate)
            SPAWN_RATE="$2"
            shift 2
            ;;
        -t|--time)
            RUN_TIME="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Error: Opción desconocida: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Verificar que Locust esté instalado
if ! command -v locust &> /dev/null; then
    echo -e "${RED}Error: Locust no está instalado${NC}"
    echo "Instala las dependencias con: pip install -r requirements.txt"
    exit 1
fi

# Crear directorio de resultados si no existe
mkdir -p results

# Configurar parámetros según el modo
case $MODE in
    interactive)
        echo -e "${GREEN}🚀 Iniciando Locust en modo interactivo${NC}"
        echo -e "${YELLOW}Host: ${HOST}${NC}"
        echo -e "${YELLOW}Abre tu navegador en: http://localhost:8089${NC}"
        echo ""
        locust -f locustfile.py --host="$HOST"
        ;;
    quick)
        USERS=5
        SPAWN_RATE=1
        RUN_TIME=1m
        echo -e "${GREEN}🚀 Ejecutando prueba rápida${NC}"
        echo -e "${YELLOW}Usuarios: ${USERS}, Spawn rate: ${SPAWN_RATE}, Tiempo: ${RUN_TIME}${NC}"
        locust -f locustfile.py \
            --host="$HOST" \
            --users=$USERS \
            --spawn-rate=$SPAWN_RATE \
            --run-time=$RUN_TIME \
            --headless \
            --html=results/quick_test_$(date +%Y%m%d_%H%M%S).html \
            --csv=results/quick_test_$(date +%Y%m%d_%H%M%S)
        ;;
    load)
        USERS=50
        SPAWN_RATE=5
        RUN_TIME=10m
        echo -e "${GREEN}🚀 Ejecutando prueba de carga${NC}"
        echo -e "${YELLOW}Usuarios: ${USERS}, Spawn rate: ${SPAWN_RATE}, Tiempo: ${RUN_TIME}${NC}"
        locust -f locustfile.py \
            --host="$HOST" \
            --users=$USERS \
            --spawn-rate=$SPAWN_RATE \
            --run-time=$RUN_TIME \
            --headless \
            --html=results/load_test_$(date +%Y%m%d_%H%M%S).html \
            --csv=results/load_test_$(date +%Y%m%d_%H%M%S)
        ;;
    stress)
        USERS=100
        SPAWN_RATE=10
        RUN_TIME=30m
        echo -e "${GREEN}🚀 Ejecutando prueba de estrés${NC}"
        echo -e "${YELLOW}Usuarios: ${USERS}, Spawn rate: ${SPAWN_RATE}, Tiempo: ${RUN_TIME}${NC}"
        locust -f locustfile.py \
            --host="$HOST" \
            --users=$USERS \
            --spawn-rate=$SPAWN_RATE \
            --run-time=$RUN_TIME \
            --headless \
            --html=results/stress_test_$(date +%Y%m%d_%H%M%S).html \
            --csv=results/stress_test_$(date +%Y%m%d_%H%M%S)
        ;;
    *)
        echo -e "${RED}Error: Modo desconocido: $MODE${NC}"
        echo "Modos disponibles: interactive, quick, load, stress"
        exit 1
        ;;
esac

echo -e "${GREEN}✅ Prueba completada${NC}"



