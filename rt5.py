import pymailtm
import json
import time
import os
import logging
import requests

# Установим логирование
logging.basicConfig(level=logging.INFO)

# Инициализация клиента Temp-Mail
client = pymailtm.Client()

# Функция для генерации данных почты
def generate_email_data():
    email_count = 0
    email_file = "emails.txt"
    
    # Проверяем, существует ли файл, если нет - создаем его
    if not os.path.exists(email_file):
        with open(email_file, 'w') as f:
            pass
    
    while True:
        try:
            domain = client.get_domains()[0]
            account = client.get_account()
            
            # Генерация пароля
            password = "password123"  # Здесь можно использовать любой генератор паролей
            token = client.get_token()

            email = account.address

            with open(email_file, "a") as file:
                file.write(f"{email}:{password}:{token}\n")
            
            email_count += 1

            # Проверка на количество почт для уведомления
            if email_count == 15:
                send_telegram_message("✅ Получено 15 почт!")

            # Проверка на достижение 2500 почт или размер файла в 9МБ
            if email_count >= 2500 or os.path.getsize(email_file) >= 9 * 1024 * 1024:
                send_file_to_telegram(email_file)
                open(email_file, 'w').close()  # Очищаем файл
                email_count = 0
            
            logging.info(f"Успешно создано: {email}:{password}:{token}")
        
        except Exception as e:
            logging.error(f"Ошибка при создании почты: {str(e)}")
        
        # Ожидание перед следующей итерацией
        time.sleep(3)

# Функция для отправки сообщения в Telegram
def send_telegram_message(message):
    bot_token = "7426380650:AAEkJp4_EF4h8ZvLxBbNNWT8xXg7jRQ02n0"
    chat_id = "7412395676"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    requests.post(url, data=payload)

# Функция для отправки файла в Telegram
def send_file_to_telegram(file_path):
    bot_token = "7426380650:AAEkJp4_EF4h8ZvLxBbNNWT8xXg7jRQ02n0"
    chat_id = "7412395676"
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    files = {"document": open(file_path, "rb")}
    data = {"chat_id": chat_id, "caption": "#почты"}
    requests.post(url, files=files, data=data)

# Основная функция
def main():
    generate_email_data()

if __name__ == "__main__":
    main()
