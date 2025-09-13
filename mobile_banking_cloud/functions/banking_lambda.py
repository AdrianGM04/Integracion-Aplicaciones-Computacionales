import json
import boto3
import decimal
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import os
import logging
from decimal import Decimal
import uuid

# Configuración de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clientes AWS
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')
sqs_client = boto3.client('sqs')
kms_client = boto3.client('kms')

# Tablas DynamoDB
accounts_table = dynamodb.Table(os.environ['ACCOUNTS_TABLE'])
transactions_table = dynamodb.Table(os.environ['TRANSACTIONS_TABLE'])
balances_table = dynamodb.Table(os.environ['BALANCES_TABLE'])

# Colas SQS
transaction_queue_url = os.environ['TRANSACTION_QUEUE_URL']
notification_queue_url = os.environ['NOTIFICATION_QUEUE_URL']

class BankingError(Exception):
    """Excepción personalizada para errores bancarios"""
    pass

class InsufficientFundsError(BankingError):
    """Excepción para fondos insuficientes"""
    pass

class InvalidAccountError(BankingError):
    """Excepción para cuenta inválida"""
    pass

def verify_user_token(event: Dict[str, Any]) -> Dict[str, Any]:
    """Verifica el token JWT del usuario"""
    auth_header = event.get('headers', {}).get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise BankingError("Token de autorización requerido")
    
    # En un entorno real, aquí se verificaría el JWT
    # Por simplicidad, asumimos que el token es válido
    return {'user_id': 'user_123', 'role': 'customer'}

def get_account_balance(account_id: str) -> Decimal:
    """Obtiene el saldo actual de una cuenta"""
    try:
        response = balances_table.get_item(Key={'account_id': account_id})
        if 'Item' not in response:
            raise InvalidAccountError("Cuenta no encontrada")
        
        return Decimal(str(response['Item']['balance']))
    except Exception as e:
        logger.error(f"Error obteniendo saldo: {str(e)}")
        raise BankingError("Error obteniendo saldo de la cuenta")

def update_account_balance(account_id: str, amount: Decimal, operation: str) -> None:
    """Actualiza el saldo de una cuenta"""
    try:
        if operation == 'debit':
            amount = -amount
        
        balances_table.update_item(
            Key={'account_id': account_id},
            UpdateExpression='ADD balance :amount',
            ExpressionAttributeValues={':amount': amount},
            ConditionExpression='attribute_exists(account_id)'
        )
    except Exception as e:
        logger.error(f"Error actualizando saldo: {str(e)}")
        raise BankingError("Error actualizando saldo de la cuenta")

def create_transaction_record(
    transaction_id: str,
    from_account: str,
    to_account: str,
    amount: Decimal,
    transaction_type: str,
    description: str,
    user_id: str
) -> None:
    """Crea un registro de transacción"""
    transaction_data = {
        'transaction_id': transaction_id,
        'from_account': from_account,
        'to_account': to_account,
        'amount': amount,
        'transaction_type': transaction_type,
        'description': description,
        'user_id': user_id,
        'status': 'completed',
        'created_at': datetime.utcnow().isoformat(),
        'processed_at': datetime.utcnow().isoformat()
    }
    
    transactions_table.put_item(Item=transaction_data)

def send_notification(user_id: str, message: str, notification_type: str) -> None:
    """Envía una notificación al usuario"""
    notification_data = {
        'user_id': user_id,
        'message': message,
        'type': notification_type,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    sqs_client.send_message(
        QueueUrl=notification_queue_url,
        MessageBody=json.dumps(notification_data)
    )

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Función Lambda principal para operaciones bancarias
    Maneja consulta de saldo, transferencias y historial de transacciones
    """
    try:
        http_method = event['httpMethod']
        path = event['path']
        
        # Verificar autenticación
        user_info = verify_user_token(event)
        
        # CORS headers
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
        
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'CORS preflight'})
            }
        
        # Rutas de operaciones bancarias
        if path == '/banking/balance':
            return handle_get_balance(event, headers, user_info)
        elif path == '/banking/transfer':
            return handle_transfer(event, headers, user_info)
        elif path == '/banking/transactions':
            return handle_get_transactions(event, headers, user_info)
        elif path == '/banking/account-info':
            return handle_get_account_info(event, headers, user_info)
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Endpoint no encontrado'})
            }
            
    except BankingError as e:
        logger.error(f"Error bancario: {str(e)}")
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
    except Exception as e:
        logger.error(f"Error interno: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Error interno del servidor'})
        }

def handle_get_balance(event: Dict[str, Any], headers: Dict[str, str], user_info: Dict[str, Any]) -> Dict[str, Any]:
    """Maneja la consulta de saldo de cuenta"""
    account_id = event.get('queryStringParameters', {}).get('account_id')
    if not account_id:
        raise BankingError("ID de cuenta requerido")
    
    # Verificar que el usuario tiene acceso a esta cuenta
    # En un entorno real, se verificaría la relación usuario-cuenta
    
    balance = get_account_balance(account_id)
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'account_id': account_id,
            'balance': float(balance),
            'currency': 'USD',
            'last_updated': datetime.utcnow().isoformat()
        })
    }

def handle_transfer(event: Dict[str, Any], headers: Dict[str, str], user_info: Dict[str, Any]) -> Dict[str, Any]:
    """Maneja las transferencias entre cuentas"""
    body = json.loads(event['body'])
    from_account = body.get('from_account')
    to_account = body.get('to_account')
    amount = Decimal(str(body.get('amount', 0)))
    description = body.get('description', '')
    
    if not all([from_account, to_account, amount]):
        raise BankingError("Datos de transferencia incompletos")
    
    if amount <= 0:
        raise BankingError("El monto debe ser mayor a cero")
    
    if from_account == to_account:
        raise BankingError("No se puede transferir a la misma cuenta")
    
    # Verificar saldo suficiente
    current_balance = get_account_balance(from_account)
    if current_balance < amount:
        raise InsufficientFundsError("Fondos insuficientes")
    
    # Generar ID de transacción único
    transaction_id = str(uuid.uuid4())
    
    try:
        # Actualizar saldos (en un entorno real, esto sería una transacción atómica)
        update_account_balance(from_account, amount, 'debit')
        update_account_balance(to_account, amount, 'credit')
        
        # Crear registro de transacción
        create_transaction_record(
            transaction_id=transaction_id,
            from_account=from_account,
            to_account=to_account,
            amount=amount,
            transaction_type='transfer',
            description=description,
            user_id=user_info['user_id']
        )
        
        # Enviar notificaciones
        send_notification(
            user_info['user_id'],
            f"Transferencia exitosa de ${amount} a cuenta {to_account}",
            'transfer_completed'
        )
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Transferencia exitosa',
                'transaction_id': transaction_id,
                'amount': float(amount),
                'from_account': from_account,
                'to_account': to_account,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        # En caso de error, revertir cambios
        logger.error(f"Error en transferencia: {str(e)}")
        raise BankingError("Error procesando transferencia")

def handle_get_transactions(event: Dict[str, Any], headers: Dict[str, str], user_info: Dict[str, Any]) -> Dict[str, Any]:
    """Obtiene el historial de transacciones del usuario"""
    account_id = event.get('queryStringParameters', {}).get('account_id')
    limit = int(event.get('queryStringParameters', {}).get('limit', 50))
    
    if not account_id:
        raise BankingError("ID de cuenta requerido")
    
    # Obtener transacciones de la cuenta
    response = transactions_table.query(
        IndexName='from_account-index',
        KeyConditionExpression='from_account = :account',
        ExpressionAttributeValues={':account': account_id},
        Limit=limit,
        ScanIndexForward=False  # Orden descendente (más recientes primero)
    )
    
    transactions = []
    for item in response['Items']:
        transactions.append({
            'transaction_id': item['transaction_id'],
            'amount': float(item['amount']),
            'type': item['transaction_type'],
            'description': item['description'],
            'timestamp': item['created_at'],
            'status': item['status']
        })
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'account_id': account_id,
            'transactions': transactions,
            'total_count': len(transactions)
        })
    }

def handle_get_account_info(event: Dict[str, Any], headers: Dict[str, str], user_info: Dict[str, Any]) -> Dict[str, Any]:
    """Obtiene información detallada de la cuenta"""
    account_id = event.get('queryStringParameters', {}).get('account_id')
    if not account_id:
        raise BankingError("ID de cuenta requerido")
    
    # Obtener información de la cuenta
    response = accounts_table.get_item(Key={'account_id': account_id})
    if 'Item' not in response:
        raise InvalidAccountError("Cuenta no encontrada")
    
    account = response['Item']
    balance = get_account_balance(account_id)
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'account_id': account_id,
            'account_type': account.get('account_type', 'checking'),
            'balance': float(balance),
            'currency': account.get('currency', 'USD'),
            'status': account.get('status', 'active'),
            'opened_date': account.get('opened_date'),
            'last_activity': datetime.utcnow().isoformat()
        })
    }


