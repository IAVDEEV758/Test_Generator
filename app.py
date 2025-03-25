from flask import Flask, request, jsonify
import requests
import os
import json
from flask_cors import CORS

app = Flask(__name__)
# Разрешаем запросы с любого домена (для теста), либо укажите конкретный домен GitHub Pages
CORS(app, resources={r"/*": {"origins": "https://iavdeev758.github.io"}}) 



app = Flask(__name__)
CORS(app)  # Разрешаем CORS для взаимодействия с фронтендом

# Данные для авторизации GigaChat
CLIENT_ID = "c527527a-82e7-44eb-bc28-1ffad1a97c39"
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SCOPE = "GIGACHAT_API_PERS"
AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

# Функция для получения токена авторизации
def get_access_token():
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": CLIENT_ID  # Уникальный идентификатор запроса
    }
    payload = {
        "scope": SCOPE,
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(AUTH_URL, headers=headers, data=payload, verify=False)  # Отключаем проверку SSL для примера
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception("Ошибка получения токена")

# Маршрут для генерации теста
@app.route('/generate_test', methods=['POST'])
def generate_test():
    topic = request.json.get('topic')
    if not topic:
        return jsonify({"error": "Тема не указана"}), 400

    prompt = f"""Создай тест по теме "{topic}". Если информация в кавычках не является темой теста, выведи ошибку.
    Формат:
    - 5 вопросов с 4 вариантами ответов каждый
    - Каждый вопрос пронумерован
    - Варианты ответов помечены буквами A-D
    - Правильный ответ выделен жирным шрифтом (**жирный текст**)
    - После каждого вопроса пустая строка"""

    try:
        access_token = get_access_token()
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
        response = requests.post(API_URL, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        result = response.json()["choices"][0]["message"]["content"]
        return jsonify({"test": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)