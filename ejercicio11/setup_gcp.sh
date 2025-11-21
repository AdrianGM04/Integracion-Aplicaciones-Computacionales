#!/bin/bash
# Script de configuración inicial para GCP Compute Engine
# Compatible con Ubuntu/Debian, CentOS/RHEL, y Fedora

set -e

echo "=========================================="
echo "Configurando aplicación Flask en GCP"
echo "=========================================="

# Detectar distribución
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
    elif [ -f /etc/redhat-release ]; then
        DISTRO="rhel"
    else
        DISTRO="unknown"
    fi
    echo $DISTRO
}

DISTRO=$(detect_distro)
echo "[*] Distribución detectada: $DISTRO"

# Función para instalar paquetes según la distribución
install_packages() {
    case $DISTRO in
        ubuntu|debian)
            echo "[*] Usando apt-get..."
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv mysql-client
            ;;
        centos|rhel|fedora|rocky|almalinux)
            echo "[*] Usando yum/dnf..."
            if command -v dnf &> /dev/null; then
                sudo dnf update -y
                sudo dnf install -y python3 python3-pip mysql
            else
                sudo yum update -y
                sudo yum install -y python3 python3-pip mysql
            fi
            ;;
        *)
            echo "[ERROR] Distribución no soportada: $DISTRO"
            echo "Por favor, instala manualmente: python3, python3-pip, mysql-client"
            exit 1
            ;;
    esac
}

# Actualizar sistema e instalar dependencias
echo "[*] Instalando dependencias del sistema..."
install_packages

# Instalar MySQL Server si no está instalado
if ! command -v mysql &> /dev/null; then
    echo "[*] Instalando MySQL Server..."
    case $DISTRO in
        ubuntu|debian)
            sudo apt-get install -y mysql-server
            sudo systemctl start mysql
            sudo systemctl enable mysql
            ;;
        centos|rhel|fedora|rocky|almalinux)
            if command -v dnf &> /dev/null; then
                sudo dnf install -y mysql-server
            else
                sudo yum install -y mysql-server
            fi
            sudo systemctl start mysqld
            sudo systemctl enable mysqld
            ;;
    esac
fi

# Crear entorno virtual
echo "[*] Creando entorno virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Instalar dependencias de Python
echo "[*] Instalando dependencias de Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Configurar MySQL
echo "[*] Configurando MySQL..."
if [ -f "schema.sql" ]; then
    echo "[*] Creando base de datos y tablas..."
    # Intentar con root sin contraseña primero
    sudo mysql < schema.sql 2>/dev/null || \
    mysql -u root -p < schema.sql 2>/dev/null || \
    echo "[WARN] Error ejecutando schema.sql, puede que necesites ejecutarlo manualmente"
fi

# Configurar MySQL para conexiones locales
echo "[*] Configurando MySQL para conexiones locales..."
MYSQL_CONF=""
case $DISTRO in
    ubuntu|debian)
        MYSQL_CONF="/etc/mysql/mysql.conf.d/mysqld.cnf"
        if [ -f "$MYSQL_CONF" ]; then
            sudo sed -i 's/bind-address.*/bind-address = 127.0.0.1/' "$MYSQL_CONF"
        fi
        ;;
    centos|rhel|fedora|rocky|almalinux)
        MYSQL_CONF="/etc/my.cnf"
        if [ -f "$MYSQL_CONF" ]; then
            sudo sed -i 's/bind-address.*/bind-address = 127.0.0.1/' "$MYSQL_CONF"
        fi
        ;;
esac

# Reiniciar MySQL
if [ -n "$MYSQL_CONF" ]; then
    case $DISTRO in
        ubuntu|debian)
            sudo systemctl restart mysql 2>/dev/null || echo "[WARN] No se pudo reiniciar MySQL"
            ;;
        centos|rhel|fedora|rocky|almalinux)
            sudo systemctl restart mysqld 2>/dev/null || echo "[WARN] No se pudo reiniciar MySQL"
            ;;
    esac
fi

# Dar permisos de ejecución al script de inicio
chmod +x start.sh

echo "=========================================="
echo "Configuración completada!"
echo "=========================================="
echo ""
echo "Para iniciar la aplicación:"
echo "  ./start.sh"
echo ""
echo "O manualmente:"
echo "  source venv/bin/activate"
echo "  python3 app2.py"
echo ""
echo "NOTA: Si el schema.sql no se ejecutó automáticamente,"
echo "ejecuta manualmente:"
echo "  sudo mysql < schema.sql"
echo "  o"
echo "  mysql -u root -p < schema.sql"
echo ""
