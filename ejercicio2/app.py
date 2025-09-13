from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import json
import os

app = Flask(__name__)
CORS(app)  # Habilitar CORS para evitar problemas de cross-origin

# Configuración de Ollama
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
MODEL_NAME = os.getenv('MODEL_NAME', 'deepseek-coder')

@app.route('/')
def index():
    """Página principal con el chatbot"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint para comunicarse con Ollama"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'Mensaje vacío'}), 400
        
        # Preparar la solicitud para Ollama
        ollama_payload = {
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "stream": False
        }
        
        # Realizar la solicitud a Ollama
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=ollama_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            ollama_response = response.json()
            bot_message = ollama_response.get('message', {}).get('content', 'No se pudo obtener respuesta')
            
            return jsonify({
                'success': True,
                'message': bot_message,
                'model': MODEL_NAME
            })
        else:
            return jsonify({
                'error': f'Error en Ollama: {response.status_code}',
                'details': response.text
            }), 500
            
    except requests.exceptions.ConnectionError:
        return jsonify({
            'error': 'No se puede conectar con Ollama. Asegúrate de que el contenedor esté ejecutándose.'
        }), 503
    except requests.exceptions.Timeout:
        return jsonify({
            'error': 'Timeout: La respuesta tardó demasiado'
        }), 504
    except Exception as e:
        return jsonify({
            'error': f'Error interno: {str(e)}'
        }), 500

@app.route('/api/health')
def health():
    """Endpoint para verificar el estado de Ollama"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return jsonify({
                'status': 'healthy',
                'ollama_url': OLLAMA_URL,
                'available_models': [model.get('name', '') for model in models]
            })
        else:
            return jsonify({
                'status': 'unhealthy',
                'error': f'Ollama responded with status {response.status_code}'
            }), 503
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
