from flask import Flask, request, jsonify, make_response
import requests
import json
import os
import base64
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Данные для авторизации GigaChat
CLIENT_ID = "c527527a-82e7-44eb-bc28-1ffad1a97c39"
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SCOPE = "GIGACHAT_API_PERS".strip()  # Убедимся, что нет лишних пробелов
AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

# Проверяем, что CLIENT_SECRET установлен
if not CLIENT_SECRET:
    app.logger.error("CLIENT_SECRET не установлен в переменных окружения")
    raise ValueError("CLIENT_SECRET не установлен")

# Удаляем возможные пробелы и переносы строк
CLIENT_ID = CLIENT_ID.strip()
CLIENT_SECRET = CLIENT_SECRET.strip()

# Формируем ключ авторизации в Base64
auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
app.logger.info(f"Строка для кодирования: {auth_string}")
auth_base64 = base64.b64encode(auth_string.encode()).decode()
app.logger.info(f"Закодированный ключ в Base64: {auth_base64}")

# Функция для получения токена авторизации
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
    app.logger.info(f"Отправляемый scope: {SCOPE}")
    app.logger.info(f"Полный payload: {payload}")
    try:
        app.logger.info("Отправка запроса на получение токена")
        response = requests.post(AUTH_URL, headers=headers, data=payload, verify=False)
        response.raise_for_status()
        app.logger.info("Токен успешно получен")
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        error_message = f"Ошибка получения токена: {str(e)}"
        if 'response' in locals():
            error_message += f" | Статус-код: {response.status_code} | Ответ: {response.text}"
        app.logger.error(error_message)
        raise Exception(error_message)

# Обработка OPTIONS для CORS
@app.route('/generate_test', methods=['OPTIONS'])
def handle_options():
    response = make_response()
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response, 200

# Маршрут для генерации теста
@app.route('/generate_test', methods=['POST'])
def generate_test():
    try:
        topic = request.json.get('topic')
        if not topic:
            app.logger.warning("Тема не указана в запросе")
            return jsonify({"error": "Тема не указана"}), 400

        app.logger.info(f"Получен запрос на тему: {topic}")

        prompt = f"""Создай тест по теме "{topic}". Если информация в кавычках не является темой теста, выведи ошибку.
        Формат:
        - 5 вопросов с 4 вариантами ответов каждый
        - Каждый вопрос пронумерован
        - Варианты ответов помечены буквами A-D
        - Правильный ответ выделен жирным шрифтом (**жирный текст**)
        - После каждого вопроса пустая строка"""

        app.logger.info("Получение токена от GigaChat")
        access_token = get_access_token()
        app.logger.info("Токен успешно получен")

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

        app.logger.info("Отправка запроса к GigaChat")
        response = requests.post(API_URL, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        result = response.json()["choices"][0]["message"]["content"]
        app.logger.info("Ответ от GigaChat успешно получен")

        return jsonify({"test": result})

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Ошибка при запросе к GigaChat: {str(e)}")
        return jsonify({"error": f"Ошибка при запросе к GigaChat: {str(e)}"}), 500
    except Exception as e:
        app.logger.error(f"Общая ошибка: {str(e)}")
        return jsonify({"error": f"Общая ошибка: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)