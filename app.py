from flask import Flask, request, jsonify, make_response
import requests
import os
import base64
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)


# Данные для авторизации GigaChat
CLIENT_ID = "c527527a-82e7-44eb-bc28-1ffad1a97c39"
CLIENT_SECRET = os.getenv("CLIENT_SECRET")  # Должен быть задан в переменной окружения
SCOPE = "GIGACHAT_API_PERS"
AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

# Проверяем, что CLIENT_SECRET установлен
if not CLIENT_SECRET:
    raise ValueError("CLIENT_SECRET не установлен в переменных окружения")

# Формируем ключ авторизации (исправлено: CLIENT_SECRET уже в Base64)
auth_base64 = CLIENT_SECRET  # Убираем лишнее кодирование

def get_access_token():
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": CLIENT_ID,
        "Authorization": f"Basic {auth_base64}"
    }
    payload = {
        "scope": SCOPE,
        "grant_type": "client_credentials"
    }
    try:
        response = requests.post(AUTH_URL, headers=headers, data=payload, verify=False)
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        return None

@app.route('/generate_test', methods=['POST', 'OPTIONS'])
def generate_test():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response, 200
    
    data = request.get_json()
    topic = data.get('topic')
    if not topic:
        return jsonify({"error": "Тема не указана"}), 400
    
    prompt = f"""Создай тест по теме "{topic}". 
    Формат:
    - 5 вопросов с 4 вариантами ответов
    - Варианты: A-D, правильный **жирным**
    """
    
    access_token = get_access_token()
    if not access_token:
        return jsonify({"error": "Не удалось получить токен"}), 500
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "model": "GigaChat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        result = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        return jsonify({"test": result})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Ошибка запроса: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)