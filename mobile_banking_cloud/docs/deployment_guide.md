# Guía de Despliegue - Aplicación de Banca Móvil

## Prerrequisitos

### Herramientas Requeridas

- **AWS CLI** v2.0+
- **Terraform** v1.0+
- **Python** 3.9+
- **Docker** (opcional, para desarrollo local)
- **Git**

### Configuración de AWS

1. **Configurar AWS CLI**:
   ```bash
   aws configure
   ```
   
   Ingresar:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Default region (ej: us-east-1)
   - Default output format (json)

2. **Verificar configuración**:
   ```bash
   aws sts get-caller-identity
   ```

3. **Crear bucket para estado de Terraform**:
   ```bash
   aws s3 mb s3://mobile-banking-terraform-state
   ```

## Configuración del Proyecto

### 1. Clonar el Repositorio

```bash
git clone <repository-url>
cd mobile_banking_cloud
```

### 2. Configurar Variables de Entorno

```bash
cp infrastructure/terraform.tfvars.example infrastructure/terraform.tfvars
```

Editar `infrastructure/terraform.tfvars` con tus valores:

```hcl
# Configuración básica
aws_region   = "us-east-1"
environment  = "dev"
project_name = "mobile-banking"

# Credenciales sensibles
db_password = "TuContraseñaSegura123!"
jwt_secret  = "tu-jwt-secret-key-de-al-menos-32-caracteres"

# Configuración de CORS
allowed_cors_origins = [
  "https://tu-app-movil.com",
  "https://tu-web-app.com"
]

# Configuración de seguridad
enable_encryption = true
enable_monitoring = true

# Notificaciones
notification_email = "admin@tudominio.com"
```

### 3. Instalar Dependencias Python

```bash
pip install -r requirements.txt
```

## Despliegue de Infraestructura

### 1. Inicializar Terraform

```bash
cd infrastructure
terraform init
```

### 2. Validar Configuración

```bash
terraform validate
```

### 3. Planificar Despliegue

```bash
terraform plan -out=tfplan
```

Revisar el plan para asegurar que todos los recursos sean creados correctamente.

### 4. Aplicar Configuración

```bash
terraform apply tfplan
```

Este proceso puede tomar 15-20 minutos para crear todos los recursos.

### 5. Verificar Despliegue

```bash
terraform output
```

Anotar los valores importantes como:
- `api_gateway_url`
- `database_endpoint`
- `redis_endpoint`

## Despliegue de Funciones Lambda

### 1. Empaquetar Funciones

```bash
# Crear directorio para paquetes
mkdir -p packages

# Empaquetar función de autenticación
cd functions
zip -r ../packages/auth_lambda.zip auth_lambda.py
cd ..

# Empaquetar función de banking
cd functions
zip -r ../packages/banking_lambda.zip banking_lambda.py
cd ..

# Empaquetar función de notificaciones
cd functions
zip -r ../packages/notifications_lambda.zip notifications_lambda.py
cd ..
```

### 2. Actualizar Funciones Lambda

```bash
# Actualizar función de autenticación
aws lambda update-function-code \
  --function-name mobile-banking-auth \
  --zip-file fileb://packages/auth_lambda.zip

# Actualizar función de banking
aws lambda update-function-code \
  --function-name mobile-banking-banking \
  --zip-file fileb://packages/banking_lambda.zip

# Actualizar función de notificaciones
aws lambda update-function-code \
  --function-name mobile-banking-notifications \
  --zip-file fileb://packages/notifications_lambda.zip
```

## Configuración de Base de Datos

### 1. Conectar a RDS

```bash
# Obtener endpoint de la base de datos
DB_ENDPOINT=$(terraform output -raw database_endpoint)

# Conectar usando psql
psql -h $DB_ENDPOINT -U dbadmin -d mobilebanking
```

### 2. Crear Tablas

```sql
-- Tabla de usuarios
CREATE TABLE users (
    user_id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'customer',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Tabla de cuentas
CREATE TABLE accounts (
    account_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    account_type VARCHAR(20) DEFAULT 'checking',
    balance DECIMAL(15,2) DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) DEFAULT 'active',
    opened_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Tabla de transacciones
CREATE TABLE transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    from_account VARCHAR(50) NOT NULL,
    to_account VARCHAR(50) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    FOREIGN KEY (from_account) REFERENCES accounts(account_id),
    FOREIGN KEY (to_account) REFERENCES accounts(account_id)
);

-- Índices para optimizar consultas
CREATE INDEX idx_transactions_from_account ON transactions(from_account);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_accounts_user_id ON accounts(user_id);
```

### 3. Insertar Datos de Prueba

```sql
-- Usuario de prueba
INSERT INTO users (user_id, username, email, full_name, password_hash) 
VALUES ('user_123', 'testuser', 'test@example.com', 'Usuario Prueba', '$2b$12$hash');

-- Cuenta de prueba
INSERT INTO accounts (account_id, user_id, balance) 
VALUES ('acc_123', 'user_123', 1000.00);
```

## Configuración de DynamoDB

### 1. Verificar Tablas Creadas

```bash
aws dynamodb list-tables
```

### 2. Insertar Datos de Prueba

```bash
# Usuario de prueba en DynamoDB
aws dynamodb put-item \
  --table-name mobile-banking-users \
  --item '{
    "username": {"S": "testuser"},
    "user_id": {"S": "user_123"},
    "email": {"S": "test@example.com"},
    "full_name": {"S": "Usuario Prueba"},
    "password_hash": {"S": "$2b$12$hash"},
    "role": {"S": "customer"},
    "is_active": {"BOOL": true},
    "created_at": {"S": "2024-01-15T10:30:00Z"}
  }'

# Saldo de prueba
aws dynamodb put-item \
  --table-name mobile-banking-balances \
  --item '{
    "account_id": {"S": "acc_123"},
    "balance": {"N": "1000.00"}
  }'
```

## Configuración de Monitoreo

### 1. Configurar CloudWatch Dashboards

```bash
# Crear dashboard de aplicación
aws cloudwatch put-dashboard \
  --dashboard-name "MobileBanking-App" \
  --dashboard-body file://monitoring/dashboard.json
```

### 2. Configurar Alertas

```bash
# Alerta de latencia alta
aws cloudwatch put-metric-alarm \
  --alarm-name "High-Latency" \
  --alarm-description "API latency is too high" \
  --metric-name Duration \
  --namespace AWS/Lambda \
  --statistic Average \
  --period 300 \
  --threshold 5000 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

## Pruebas Post-Despliegue

### 1. Probar Autenticación

```bash
# Obtener URL del API Gateway
API_URL=$(terraform output -raw api_gateway_url)

# Probar login
curl -X POST $API_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123",
    "device_info": {
      "device_id": "test-device",
      "platform": "ios"
    }
  }'
```

### 2. Probar Operaciones Bancarias

```bash
# Obtener token del login anterior
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Probar consulta de saldo
curl -X GET "$API_URL/banking/balance?account_id=acc_123" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Probar Notificaciones

```bash
# Enviar notificación de prueba
curl -X POST $API_URL/notifications/send \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "message": "Prueba de notificación",
    "type": "test",
    "channels": ["push"]
  }'
```

## Configuración de CI/CD

### 1. GitHub Actions

Crear `.github/workflows/deploy.yml`:

```yaml
name: Deploy Mobile Banking

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python -m pytest tests/
    
    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v1
    
    - name: Terraform Plan
      run: |
        cd infrastructure
        terraform plan
    
    - name: Terraform Apply
      if: github.ref == 'refs/heads/main'
      run: |
        cd infrastructure
        terraform apply -auto-approve
```

### 2. Variables de Entorno en GitHub

Configurar los siguientes secrets en GitHub:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `DB_PASSWORD`
- `JWT_SECRET`

## Rollback y Recuperación

### 1. Rollback de Infraestructura

```bash
# Ver historial de cambios
terraform show

# Rollback a versión anterior
terraform apply -target=aws_lambda_function.auth
```

### 2. Rollback de Funciones Lambda

```bash
# Listar versiones
aws lambda list-versions-by-function --function-name mobile-banking-auth

# Rollback a versión anterior
aws lambda update-alias \
  --function-name mobile-banking-auth \
  --name PROD \
  --function-version 2
```

### 3. Restaurar Base de Datos

```bash
# Crear snapshot
aws rds create-db-snapshot \
  --db-instance-identifier mobile-banking-db \
  --db-snapshot-identifier mobile-banking-backup-$(date +%Y%m%d)

# Restaurar desde snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier mobile-banking-db-restored \
  --db-snapshot-identifier mobile-banking-backup-20240115
```

## Mantenimiento

### 1. Actualizaciones de Seguridad

```bash
# Actualizar dependencias Python
pip install --upgrade -r requirements.txt

# Actualizar funciones Lambda
aws lambda update-function-code --function-name mobile-banking-auth --zip-file fileb://packages/auth_lambda.zip
```

### 2. Monitoreo de Costos

```bash
# Ver costos por servicio
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE
```

### 3. Limpieza de Logs

```bash
# Configurar retención de logs
aws logs put-retention-policy \
  --log-group-name /aws/lambda/mobile-banking-auth \
  --retention-in-days 14
```

## Troubleshooting

### Problemas Comunes

1. **Error de conexión a RDS**:
   - Verificar security groups
   - Confirmar que la instancia está en subnets privadas

2. **Lambda timeout**:
   - Aumentar timeout en configuración
   - Optimizar código para mejor rendimiento

3. **DynamoDB throttling**:
   - Aumentar capacidad de lectura/escritura
   - Implementar backoff exponencial

4. **API Gateway 502**:
   - Verificar configuración de Lambda
   - Revisar logs de CloudWatch

### Comandos de Diagnóstico

```bash
# Ver logs de Lambda
aws logs tail /aws/lambda/mobile-banking-auth --follow

# Ver métricas de CloudWatch
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=mobile-banking-auth \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z \
  --period 300 \
  --statistics Average
```


