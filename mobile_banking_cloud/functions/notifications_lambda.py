import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import os
import logging
import uuid

# Configuración de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clientes AWS
sns_client = boto3.client('sns')
sqs_client = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')
cloudtrail_client = boto3.client('cloudtrail')
firehose_client = boto3.client('firehose')

# Tablas DynamoDB
notifications_table = dynamodb.Table(os.environ['NOTIFICATIONS_TABLE'])
audit_logs_table = dynamodb.Table(os.environ['AUDIT_LOGS_TABLE'])
user_preferences_table = dynamodb.Table(os.environ['USER_PREFERENCES_TABLE'])

# Colas SQS
notification_queue_url = os.environ['NOTIFICATION_QUEUE_URL']
audit_queue_url = os.environ['AUDIT_QUEUE_URL']

# Topics SNS
push_notification_topic = os.environ['PUSH_NOTIFICATION_TOPIC']
email_notification_topic = os.environ['EMAIL_NOTIFICATION_TOPIC']

class NotificationError(Exception):
    """Excepción personalizada para errores de notificaciones"""
    pass

class AuditError(Exception):
    """Excepción personalizada para errores de auditoría"""
    pass

def log_audit_event(
    user_id: str,
    action: str,
    resource: str,
    details: Dict[str, Any],
    ip_address: str = None,
    user_agent: str = None
) -> None:
    """Registra un evento de auditoría"""
    audit_id = str(uuid.uuid4())
    audit_data = {
        'audit_id': audit_id,
        'user_id': user_id,
        'action': action,
        'resource': resource,
        'details': details,
        'ip_address': ip_address,
        'user_agent': user_agent,
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'logged'
    }
    
    # Guardar en DynamoDB
    audit_logs_table.put_item(Item=audit_data)
    
    # Enviar a cola para procesamiento adicional
    sqs_client.send_message(
        QueueUrl=audit_queue_url,
        MessageBody=json.dumps(audit_data)
    )

def get_user_notification_preferences(user_id: str) -> Dict[str, Any]:
    """Obtiene las preferencias de notificación del usuario"""
    try:
        response = user_preferences_table.get_item(Key={'user_id': user_id})
        if 'Item' in response:
            return response['Item'].get('notification_preferences', {})
        else:
            # Preferencias por defecto
            return {
                'push_enabled': True,
                'email_enabled': True,
                'sms_enabled': False,
                'transaction_alerts': True,
                'security_alerts': True,
                'marketing_alerts': False
            }
    except Exception as e:
        logger.error(f"Error obteniendo preferencias: {str(e)}")
        return {}

def send_push_notification(user_id: str, message: str, notification_type: str) -> None:
    """Envía una notificación push"""
    try:
        notification_data = {
            'user_id': user_id,
            'message': message,
            'type': notification_type,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        sns_client.publish(
            TopicArn=push_notification_topic,
            Message=json.dumps(notification_data),
            Subject=f"Notificación Bancaria - {notification_type}"
        )
        
        logger.info(f"Notificación push enviada a usuario {user_id}")
        
    except Exception as e:
        logger.error(f"Error enviando notificación push: {str(e)}")
        raise NotificationError("Error enviando notificación push")

def send_email_notification(user_id: str, subject: str, message: str) -> None:
    """Envía una notificación por email"""
    try:
        email_data = {
            'user_id': user_id,
            'subject': subject,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        sns_client.publish(
            TopicArn=email_notification_topic,
            Message=json.dumps(email_data),
            Subject=subject
        )
        
        logger.info(f"Email enviado a usuario {user_id}")
        
    except Exception as e:
        logger.error(f"Error enviando email: {str(e)}")
        raise NotificationError("Error enviando email")

def create_notification_record(
    user_id: str,
    message: str,
    notification_type: str,
    channels: List[str],
    status: str = 'sent'
) -> str:
    """Crea un registro de notificación"""
    notification_id = str(uuid.uuid4())
    notification_data = {
        'notification_id': notification_id,
        'user_id': user_id,
        'message': message,
        'type': notification_type,
        'channels': channels,
        'status': status,
        'created_at': datetime.utcnow().isoformat(),
        'sent_at': datetime.utcnow().isoformat() if status == 'sent' else None
    }
    
    notifications_table.put_item(Item=notification_data)
    return notification_id

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Función Lambda principal para notificaciones y auditoría
    Maneja envío de notificaciones, registro de auditoría y gestión de preferencias
    """
    try:
        http_method = event['httpMethod']
        path = event['path']
        
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
        
        # Rutas de notificaciones y auditoría
        if path == '/notifications/send':
            return handle_send_notification(event, headers)
        elif path == '/notifications/preferences':
            return handle_notification_preferences(event, headers)
        elif path == '/notifications/history':
            return handle_notification_history(event, headers)
        elif path == '/audit/log':
            return handle_log_audit(event, headers)
        elif path == '/audit/query':
            return handle_audit_query(event, headers)
        elif path == '/notifications/process-queue':
            return handle_process_notification_queue(event, headers)
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Endpoint no encontrado'})
            }
            
    except NotificationError as e:
        logger.error(f"Error de notificación: {str(e)}")
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
    except AuditError as e:
        logger.error(f"Error de auditoría: {str(e)}")
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

def handle_send_notification(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Maneja el envío de notificaciones"""
    body = json.loads(event['body'])
    user_id = body.get('user_id')
    message = body.get('message')
    notification_type = body.get('type', 'general')
    channels = body.get('channels', ['push'])
    
    if not all([user_id, message]):
        raise NotificationError("user_id y message son requeridos")
    
    # Obtener preferencias del usuario
    preferences = get_user_notification_preferences(user_id)
    
    # Filtrar canales según preferencias
    enabled_channels = []
    for channel in channels:
        if channel == 'push' and preferences.get('push_enabled', True):
            enabled_channels.append('push')
        elif channel == 'email' and preferences.get('email_enabled', True):
            enabled_channels.append('email')
        elif channel == 'sms' and preferences.get('sms_enabled', False):
            enabled_channels.append('sms')
    
    # Enviar notificaciones por canales habilitados
    notification_id = create_notification_record(
        user_id=user_id,
        message=message,
        notification_type=notification_type,
        channels=enabled_channels
    )
    
    # Enviar por cada canal
    for channel in enabled_channels:
        if channel == 'push':
            send_push_notification(user_id, message, notification_type)
        elif channel == 'email':
            send_email_notification(user_id, f"Notificación Bancaria - {notification_type}", message)
    
    # Log de auditoría
    log_audit_event(
        user_id=user_id,
        action='notification_sent',
        resource=f'notification/{notification_id}',
        details={
            'type': notification_type,
            'channels': enabled_channels,
            'message_length': len(message)
        }
    )
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'message': 'Notificación enviada exitosamente',
            'notification_id': notification_id,
            'channels_used': enabled_channels
        })
    }

def handle_notification_preferences(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Maneja las preferencias de notificación del usuario"""
    if event['httpMethod'] == 'GET':
        # Obtener preferencias
        user_id = event.get('queryStringParameters', {}).get('user_id')
        if not user_id:
            raise NotificationError("user_id requerido")
        
        preferences = get_user_notification_preferences(user_id)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'user_id': user_id,
                'preferences': preferences
            })
        }
    
    elif event['httpMethod'] == 'PUT':
        # Actualizar preferencias
        body = json.loads(event['body'])
        user_id = body.get('user_id')
        preferences = body.get('preferences', {})
        
        if not user_id:
            raise NotificationError("user_id requerido")
        
        user_preferences_table.put_item(Item={
            'user_id': user_id,
            'notification_preferences': preferences,
            'updated_at': datetime.utcnow().isoformat()
        })
        
        # Log de auditoría
        log_audit_event(
            user_id=user_id,
            action='preferences_updated',
            resource=f'user/{user_id}',
            details={'preferences': preferences}
        )
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Preferencias actualizadas exitosamente',
                'preferences': preferences
            })
        }

def handle_notification_history(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Obtiene el historial de notificaciones del usuario"""
    user_id = event.get('queryStringParameters', {}).get('user_id')
    limit = int(event.get('queryStringParameters', {}).get('limit', 50))
    
    if not user_id:
        raise NotificationError("user_id requerido")
    
    # Obtener notificaciones del usuario
    response = notifications_table.query(
        IndexName='user_id-index',
        KeyConditionExpression='user_id = :user_id',
        ExpressionAttributeValues={':user_id': user_id},
        Limit=limit,
        ScanIndexForward=False  # Orden descendente
    )
    
    notifications = []
    for item in response['Items']:
        notifications.append({
            'notification_id': item['notification_id'],
            'message': item['message'],
            'type': item['type'],
            'channels': item['channels'],
            'status': item['status'],
            'created_at': item['created_at'],
            'sent_at': item.get('sent_at')
        })
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'user_id': user_id,
            'notifications': notifications,
            'total_count': len(notifications)
        })
    }

def handle_log_audit(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Registra un evento de auditoría"""
    body = json.loads(event['body'])
    user_id = body.get('user_id')
    action = body.get('action')
    resource = body.get('resource')
    details = body.get('details', {})
    
    if not all([user_id, action, resource]):
        raise AuditError("user_id, action y resource son requeridos")
    
    # Obtener información adicional del request
    ip_address = event.get('requestContext', {}).get('identity', {}).get('sourceIp')
    user_agent = event.get('headers', {}).get('User-Agent')
    
    log_audit_event(
        user_id=user_id,
        action=action,
        resource=resource,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'message': 'Evento de auditoría registrado exitosamente'
        })
    }

def handle_audit_query(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Consulta eventos de auditoría"""
    user_id = event.get('queryStringParameters', {}).get('user_id')
    action = event.get('queryStringParameters', {}).get('action')
    start_date = event.get('queryStringParameters', {}).get('start_date')
    end_date = event.get('queryStringParameters', {}).get('end_date')
    limit = int(event.get('queryStringParameters', {}).get('limit', 100))
    
    if not user_id:
        raise AuditError("user_id requerido")
    
    # Construir query
    key_condition = 'user_id = :user_id'
    expression_values = {':user_id': user_id}
    
    if action:
        key_condition += ' AND action = :action'
        expression_values[':action'] = action
    
    # Obtener eventos de auditoría
    response = audit_logs_table.query(
        IndexName='user_id-index',
        KeyConditionExpression=key_condition,
        ExpressionAttributeValues=expression_values,
        Limit=limit,
        ScanIndexForward=False
    )
    
    # Filtrar por fecha si se proporciona
    audit_events = []
    for item in response['Items']:
        event_date = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            if event_date < start_dt:
                continue
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            if event_date > end_dt:
                continue
        
        audit_events.append({
            'audit_id': item['audit_id'],
            'action': item['action'],
            'resource': item['resource'],
            'details': item['details'],
            'timestamp': item['timestamp'],
            'ip_address': item.get('ip_address'),
            'user_agent': item.get('user_agent')
        })
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'user_id': user_id,
            'audit_events': audit_events,
            'total_count': len(audit_events)
        })
    }

def handle_process_notification_queue(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Procesa mensajes de la cola de notificaciones"""
    try:
        # Obtener mensajes de la cola
        response = sqs_client.receive_message(
            QueueUrl=notification_queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=5
        )
        
        processed_messages = []
        
        for message in response.get('Messages', []):
            try:
                # Procesar mensaje
                notification_data = json.loads(message['Body'])
                
                # Aquí se procesaría la notificación según el tipo
                # Por ejemplo, enviar push notification, email, etc.
                
                processed_messages.append({
                    'message_id': message['MessageId'],
                    'status': 'processed'
                })
                
                # Eliminar mensaje de la cola
                sqs_client.delete_message(
                    QueueUrl=notification_queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )
                
            except Exception as e:
                logger.error(f"Error procesando mensaje: {str(e)}")
                processed_messages.append({
                    'message_id': message['MessageId'],
                    'status': 'error',
                    'error': str(e)
                })
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Cola procesada',
                'processed_messages': processed_messages
            })
        }
        
    except Exception as e:
        logger.error(f"Error procesando cola: {str(e)}")
        raise NotificationError("Error procesando cola de notificaciones")


