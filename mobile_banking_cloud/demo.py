#!/usr/bin/env python3
"""
Script de demostración para la aplicación de banca móvil
Simula operaciones básicas del sistema
"""

import json
import requests
import time
from datetime import datetime

class MobileBankingDemo:
    def __init__(self, api_base_url):
        self.api_base_url = api_base_url
        self.token = None
        self.session_id = None
        
    def login(self, username, password):
        """Simula el proceso de login"""
        print(f"🔐 Iniciando sesión para usuario: {username}")
        
        login_data = {
            "username": username,
            "password": password,
            "device_info": {
                "device_id": "demo-device-123",
                "platform": "ios",
                "app_version": "1.0.0"
            }
        }
        
        try:
            response = requests.post(
                f"{self.api_base_url}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["token"]
                self.session_id = data["session_id"]
                print(f"✅ Login exitoso!")
                print(f"   Usuario: {data['user']['username']}")
                print(f"   Email: {data['user']['email']}")
                print(f"   Rol: {data['user']['role']}")
                return True
            else:
                print(f"❌ Error en login: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
            return False
    
    def get_balance(self, account_id):
        """Consulta el saldo de una cuenta"""
        print(f"💰 Consultando saldo de cuenta: {account_id}")
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.api_base_url}/banking/balance",
                params={"account_id": account_id},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Saldo actual: ${data['balance']} {data['currency']}")
                print(f"   Última actualización: {data['last_updated']}")
                return data["balance"]
            else:
                print(f"❌ Error consultando saldo: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
            return None
    
    def transfer_money(self, from_account, to_account, amount, description):
        """Realiza una transferencia"""
        print(f"💸 Realizando transferencia de ${amount} de {from_account} a {to_account}")
        
        transfer_data = {
            "from_account": from_account,
            "to_account": to_account,
            "amount": amount,
            "description": description
        }
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.api_base_url}/banking/transfer",
                json=transfer_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Transferencia exitosa!")
                print(f"   ID de transacción: {data['transaction_id']}")
                print(f"   Monto: ${data['amount']}")
                print(f"   Timestamp: {data['timestamp']}")
                return data["transaction_id"]
            else:
                print(f"❌ Error en transferencia: {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
            return None
    
    def get_transactions(self, account_id, limit=10):
        """Obtiene el historial de transacciones"""
        print(f"📋 Obteniendo historial de transacciones para cuenta: {account_id}")
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.api_base_url}/banking/transactions",
                params={"account_id": account_id, "limit": limit},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Historial obtenido ({data['total_count']} transacciones)")
                
                for i, transaction in enumerate(data["transactions"], 1):
                    print(f"   {i}. {transaction['type']} - ${transaction['amount']}")
                    print(f"      Descripción: {transaction['description']}")
                    print(f"      Fecha: {transaction['timestamp']}")
                    print(f"      Estado: {transaction['status']}")
                    print()
                
                return data["transactions"]
            else:
                print(f"❌ Error obteniendo historial: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
            return None
    
    def send_notification(self, user_id, message, notification_type):
        """Envía una notificación"""
        print(f"📱 Enviando notificación a usuario: {user_id}")
        
        notification_data = {
            "user_id": user_id,
            "message": message,
            "type": notification_type,
            "channels": ["push", "email"]
        }
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.api_base_url}/notifications/send",
                json=notification_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Notificación enviada!")
                print(f"   ID: {data['notification_id']}")
                print(f"   Canales: {', '.join(data['channels_used'])}")
                return data["notification_id"]
            else:
                print(f"❌ Error enviando notificación: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
            return None
    
    def logout(self):
        """Cierra la sesión"""
        print("🚪 Cerrando sesión...")
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Session-ID": self.session_id,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.api_base_url}/auth/logout",
                headers=headers
            )
            
            if response.status_code == 200:
                print("✅ Sesión cerrada exitosamente")
                self.token = None
                self.session_id = None
            else:
                print(f"❌ Error cerrando sesión: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")

def main():
    """Función principal de demostración"""
    print("🏦 DEMO - Aplicación de Banca Móvil")
    print("=" * 50)
    
    # Configuración
    API_BASE_URL = "https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/dev"
    
    # Crear instancia del demo
    demo = MobileBankingDemo(API_BASE_URL)
    
    # Datos de prueba
    username = "testuser"
    password = "password123"
    user_id = "user_123"
    account_id = "acc_123"
    
    print(f"🌐 Conectando a: {API_BASE_URL}")
    print()
    
    # 1. Login
    if not demo.login(username, password):
        print("❌ No se pudo iniciar sesión. Terminando demo.")
        return
    
    print()
    
    # 2. Consultar saldo
    balance = demo.get_balance(account_id)
    print()
    
    # 3. Realizar transferencia
    if balance and balance > 100:
        transaction_id = demo.transfer_money(
            from_account=account_id,
            to_account="acc_456",
            amount=50.00,
            description="Transferencia de prueba - Demo"
        )
        print()
        
        # 4. Enviar notificación
        if transaction_id:
            demo.send_notification(
                user_id=user_id,
                message=f"Su transferencia de $50.00 ha sido procesada exitosamente. ID: {transaction_id}",
                notification_type="transfer_completed"
            )
            print()
    
    # 5. Consultar historial
    demo.get_transactions(account_id, limit=5)
    
    # 6. Logout
    demo.logout()
    
    print()
    print("🎉 Demo completado exitosamente!")
    print("=" * 50)

if __name__ == "__main__":
    main()
