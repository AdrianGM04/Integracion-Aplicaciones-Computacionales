# Documentación de APIs - Aplicación de Banca Móvil

## Autenticación y Autorización

### POST /auth/login
Autentica un usuario y retorna un token JWT.

**Request Body:**
```json
{
  "username": "usuario123",
  "password": "password123",
  "device_info": {
    "device_id": "device-uuid",
    "platform": "ios",
    "app_version": "1.0.0"
  }
}
```

**Response:**
```json
{
  "message": "Login exitoso",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "session_id": "session-uuid",
  "user": {
    "user_id": "user_123",
    "username": "usuario123",
    "email": "usuario@email.com",
    "role": "customer",
    "last_login": "2024-01-15T10:30:00Z"
  }
}
```

### POST /auth/register
Registra un nuevo usuario en el sistema.

**Request Body:**
```json
{
  "username": "nuevo_usuario",
  "password": "password123",
  "email": "usuario@email.com",
  "full_name": "Juan Pérez"
}
```

**Response:**
```json
{
  "message": "Usuario registrado exitosamente",
  "user_id": "user_456"
}
```

### GET /auth/verify
Verifica la validez de un token JWT.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "message": "Token válido",
  "user_id": "user_123",
  "role": "customer"
}
```

## Operaciones Bancarias

### GET /banking/balance
Obtiene el saldo actual de una cuenta.

**Query Parameters:**
- `account_id`: ID de la cuenta

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "account_id": "acc_123",
  "balance": 1500.75,
  "currency": "USD",
  "last_updated": "2024-01-15T10:30:00Z"
}
```

### POST /banking/transfer
Realiza una transferencia entre cuentas.

**Request Body:**
```json
{
  "from_account": "acc_123",
  "to_account": "acc_456",
  "amount": 100.00,
  "description": "Transferencia a familia"
}
```

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "message": "Transferencia exitosa",
  "transaction_id": "txn_789",
  "amount": 100.00,
  "from_account": "acc_123",
  "to_account": "acc_456",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### GET /banking/transactions
Obtiene el historial de transacciones de una cuenta.

**Query Parameters:**
- `account_id`: ID de la cuenta
- `limit`: Número máximo de transacciones (default: 50)

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "account_id": "acc_123",
  "transactions": [
    {
      "transaction_id": "txn_789",
      "amount": 100.00,
      "type": "transfer",
      "description": "Transferencia a familia",
      "timestamp": "2024-01-15T10:30:00Z",
      "status": "completed"
    }
  ],
  "total_count": 1
}
```

## Notificaciones

### POST /notifications/send
Envía una notificación al usuario.

**Request Body:**
```json
{
  "user_id": "user_123",
  "message": "Su transferencia ha sido procesada exitosamente",
  "type": "transfer_completed",
  "channels": ["push", "email"]
}
```

**Response:**
```json
{
  "message": "Notificación enviada exitosamente",
  "notification_id": "notif_123",
  "channels_used": ["push", "email"]
}
```

### GET /notifications/preferences
Obtiene las preferencias de notificación del usuario.

**Query Parameters:**
- `user_id`: ID del usuario

**Response:**
```json
{
  "user_id": "user_123",
  "preferences": {
    "push_enabled": true,
    "email_enabled": true,
    "sms_enabled": false,
    "transaction_alerts": true,
    "security_alerts": true,
    "marketing_alerts": false
  }
}
```

### PUT /notifications/preferences
Actualiza las preferencias de notificación del usuario.

**Request Body:**
```json
{
  "user_id": "user_123",
  "preferences": {
    "push_enabled": true,
    "email_enabled": false,
    "sms_enabled": true,
    "transaction_alerts": true,
    "security_alerts": true,
    "marketing_alerts": false
  }
}
```

**Response:**
```json
{
  "message": "Preferencias actualizadas exitosamente",
  "preferences": {
    "push_enabled": true,
    "email_enabled": false,
    "sms_enabled": true,
    "transaction_alerts": true,
    "security_alerts": true,
    "marketing_alerts": false
  }
}
```

## Auditoría

### POST /audit/log
Registra un evento de auditoría.

**Request Body:**
```json
{
  "user_id": "user_123",
  "action": "login_attempt",
  "resource": "auth/login",
  "details": {
    "ip_address": "192.168.1.1",
    "user_agent": "Mobile App 1.0.0",
    "success": true
  }
}
```

**Response:**
```json
{
  "message": "Evento de auditoría registrado exitosamente"
}
```

### GET /audit/query
Consulta eventos de auditoría.

**Query Parameters:**
- `user_id`: ID del usuario
- `action`: Tipo de acción (opcional)
- `start_date`: Fecha de inicio (ISO 8601)
- `end_date`: Fecha de fin (ISO 8601)
- `limit`: Número máximo de eventos (default: 100)

**Response:**
```json
{
  "user_id": "user_123",
  "audit_events": [
    {
      "audit_id": "audit_456",
      "action": "login_attempt",
      "resource": "auth/login",
      "details": {
        "ip_address": "192.168.1.1",
        "user_agent": "Mobile App 1.0.0",
        "success": true
      },
      "timestamp": "2024-01-15T10:30:00Z",
      "ip_address": "192.168.1.1",
      "user_agent": "Mobile App 1.0.0"
    }
  ],
  "total_count": 1
}
```

## Códigos de Error

### 400 Bad Request
```json
{
  "error": "Datos de entrada inválidos",
  "code": "INVALID_INPUT",
  "details": "El campo 'amount' es requerido"
}
```

### 401 Unauthorized
```json
{
  "error": "Token de autorización requerido",
  "code": "UNAUTHORIZED"
}
```

### 403 Forbidden
```json
{
  "error": "Acceso denegado",
  "code": "FORBIDDEN",
  "details": "No tiene permisos para acceder a esta cuenta"
}
```

### 404 Not Found
```json
{
  "error": "Recurso no encontrado",
  "code": "NOT_FOUND",
  "details": "La cuenta especificada no existe"
}
```

### 500 Internal Server Error
```json
{
  "error": "Error interno del servidor",
  "code": "INTERNAL_ERROR",
  "details": "Error procesando la solicitud"
}
```

## Rate Limiting

- **Límite general**: 1000 requests por hora por IP
- **Límite de autenticación**: 10 intentos por minuto por usuario
- **Límite de transferencias**: 50 transferencias por día por usuario
- **Límite de consultas**: 100 consultas por minuto por usuario

## Autenticación

Todas las APIs requieren autenticación mediante JWT tokens en el header `Authorization`:

```
Authorization: Bearer <jwt_token>
```

Los tokens tienen una validez de 24 horas y pueden ser renovados usando el endpoint `/auth/refresh`.

## CORS

La API soporta CORS para requests desde aplicaciones web. Los headers permitidos son:

- `Content-Type`
- `Authorization`
- `X-Session-ID`

Los métodos HTTP permitidos son:
- `GET`
- `POST`
- `PUT`
- `DELETE`
- `OPTIONS`


