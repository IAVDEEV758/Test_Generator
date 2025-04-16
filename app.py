from flask import Flask, request, jsonify, make_response
import requests
import os
import base64
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Данные для авторизации GigaChat
CLIENT_ID = "c527527a-82e7-44eb-bc28-1ffad1a97c39"
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SCOPE = "GIGACHAT_API_PERS"
AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

# Проверяем, что CLIENT_SECRET установлен
if not CLIENT_SECRET:
    app.logger.error("CLIENT_SECRET не установлен в переменных окружения")
    raise ValueError("CLIENT_SECRET не установлен")

# Формируем ключ авторизации
auth_base64 = CLIENT_SECRET

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
        app.logger.info("Отправка запроса на получение токена")
        response = requests.post(AUTH_URL, headers=headers, data=payload, verify=False)
        response.raise_for_status()
        app.logger.info("Токен успешно получен")
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Ошибка получения токена: {str(e)}")
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
    difficulty = data.get('difficulty')
    question_type = data.get('questionType')
    question_count = data.get('questionCount')

    if not topic:
        app.logger.warning("Тема не указана в запросе")
        return jsonify({"error": "Тема не указана"}), 400
    
    if not difficulty or not question_type or not question_count:
        app.logger.warning("Не указаны параметры теста (сложность, тип вопросов или количество)")
        return jsonify({"error": "Не указаны параметры теста"}), 400

    # Преобразуем сложность в читаемый формат
    difficulty_map = {
        "1_class": "учеников 1 класса",
        "2_class": "учеников 2 класса",
        "3_class": "учеников 3 класса",
        "4_class": "учеников 4 класса",
        "5_class": "учеников 5 класса",
        "6_class": "учеников 6 класса",
        "7_class": "учеников 7 класса",
        "8_class": "учеников 8 класса",
        "9_class": "учеников 9 класса",
        "10_class": "учеников 10 класса",
        "11_class": "учеников 11 класса",
        "student": "студента"
    }
    difficulty_text = difficulty_map.get(difficulty)

    # Определяем формат вопросов
    if question_type == "open":
        question_format = "вопросы с открытым ответом (без вариантов ответа)"
    elif question_type == "2_options":
        question_format = "вопросы с 2 вариантами ответа (правильный помечен звездочкой *)"
    elif question_type == "3_options":
        question_format = "вопросы с 3 вариантами ответа (правильный помечен звездочкой *)"
    else:  # 4_options
        question_format = "вопросы с 4 вариантами ответа (правильный помечен звездочкой *)"

    # Формируем промпт
    prompt = f"""Создай тест по теме "{topic}" для {difficulty_text}. 
    Формат:
    - в ответе должен быть только тест без лишних слов
    - {question_count} вопросов
    - {question_format}
    - каждый вопрос пронумерован
    - после каждого вопроса пустая строка
    """

    app.logger.info(f"Сформированный промпт: {prompt}")

    access_token = get_access_token()
    if not access_token:
        app.logger.error("Не удалось получить токен")
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
        app.logger.info("Отправка запроса к GigaChat")
        response = requests.post(API_URL, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        result = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        app.logger.info("Ответ от GigaChat успешно получен")
        return jsonify({"test": result})
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Ошибка запроса к GigaChat: {str(e)}")
        return jsonify({"error": f"Ошибка запроса: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)