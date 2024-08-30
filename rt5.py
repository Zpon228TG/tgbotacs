import time
import os
import requests
import telebot

# Настройки Telegram
TELEGRAM_TOKEN = '7426380650:AAEkJp4_EF4h8ZvLxBbNNWT8xXg7jRQ02n0'
CHAT_ID = '7412395676'
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Настройки Temp Mail
BASE_URL = 'https://api.mail.tm'
FILE_PATH = 'emails.txt'
MAX_FILE_SIZE_MB = 9
MAX_RECORDS = 2500

# Получение списка доменов
def get_domains():
    response = requests.get(f"{BASE_URL}/domains")
    response.raise_for_status()
    return response.json()

# Создание нового аккаунта
def create_account(email, password):
    token = get_token(email, password)
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.post(f"{BASE_URL}/accounts", json={"address": email, "password": password}, headers=headers)
    response.raise_for_status()
    return response.json()['id']

# Получение токена для аккаунта
def get_token(email, password):
    response = requests.post(f"{BASE_URL}/token", json={"address": email, "password": password})
    response.raise_for_status()
    return response.json()['token']

# Получение сообщений для аккаунта
def get_messages(account_id, token):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f"{BASE_URL}/messages", headers=headers)
    response.raise_for_status()
    return response.json()['hydra:member']

# Отправка файла в Telegram
def send_file_to_telegram(file_path):
    with open(file_path, 'rb') as file:
        bot.send_document(chat_id=CHAT_ID, document=file, caption='#почты')

# Уведомление пользователя
def notify_user(message):
    bot.send_message(chat_id=CHAT_ID, text=message)

# Основная функция
def main():
    email_records = []
    domains = get_domains()
    domain = domains['hydra:member'][0]['domain']
    email = f"user@{domain}"
    password = 'your_password'  # Используйте подходящий пароль

    account_id = create_account(email, password)
    token = get_token(email, password)

    while True:
        messages = get_messages(account_id, token)
        for message in messages:
            email_records.append(f"{email}:{password}:{message['id']}\n")

            # Запись в файл и отправка, если достигнут лимит
            if len(email_records) >= MAX_RECORDS or (os.path.exists(FILE_PATH) and os.path.getsize(FILE_PATH) / (1024 * 1024) >= MAX_FILE_SIZE_MB):
                with open(FILE_PATH, 'a') as file:
                    file.writelines(email_records)

                send_file_to_telegram(FILE_PATH)
                email_records = []

                if os.path.exists(FILE_PATH):
                    os.remove(FILE_PATH)
                
                notify_user(f"Файл с почтами отправлен. Всего почт: {len(email_records)}")

        time.sleep(3)

if __name__ == "__main__":
    main()
