import requests
import json
import time
import os
import random
import string
from telebot import TeleBot

# Настройки
TELEGRAM_BOT_TOKEN = '7426380650:AAEkJp4_EF4h8ZvLxBbNNWT8xXg7jRQ02n0'
CHAT_ID = '7412395676'
FILE_PATH = 'emails.txt'
MAX_FILE_SIZE_MB = 9
API_BASE_URL = 'https://api.mail.tm'
REQUEST_LIMIT = 10  # Количество запросов до ожидания
WAIT_TIME = 60      # Время ожидания при ошибке 429 (в секундах)
MIN_WAIT_TIME = 10  # Минимальное время ожидания (в секундах)
MAX_WAIT_TIME = 25  # Максимальное время ожидания (в секундах)

# Инициализация бота
bot = TeleBot(TELEGRAM_BOT_TOKEN)

def generate_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

def generate_email(domain):
    username = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return f'{username}@{domain}'

def get_domains():
    try:
        response = requests.get(f'{API_BASE_URL}/domains')
        response.raise_for_status()
        domains = response.json()["hydra:member"]
        return [domain["domain"] for domain in domains]
    except requests.exceptions.HTTPError as e:
        bot.send_message(CHAT_ID, f"🚨 Ошибка при получении доменов: {e}")
        return []

def create_account_and_get_token(domain):
    email = generate_email(domain)
    password = generate_password()
    account_data = {
        "address": email,
        "password": password
    }
    
    try:
        response = requests.post(f'{API_BASE_URL}/accounts', json=account_data)
        if response.status_code == 429:
            bot.send_message(CHAT_ID, "🚨 Слишком много запросов, делаем паузу...")
            time.sleep(WAIT_TIME)
            return None, None, None
        
        response.raise_for_status()
        account_info = response.json()
        account_id = account_info.get('id')
        
        token_data = {
            "address": email,
            "password": password
        }
        response = requests.post(f'{API_BASE_URL}/token', json=token_data)
        if response.status_code == 429:
            bot.send_message(CHAT_ID, "🚨 Слишком много запросов, делаем паузу...")
            time.sleep(WAIT_TIME)
            return None, None, None
        
        response.raise_for_status()
        token_info = response.json()
        token = token_info.get('token')
        
        if not token:
            bot.send_message(CHAT_ID, f"🚨 Не удалось получить токен для почты {email}.")
            return None, None, None
        
        return email, password, token
    except requests.exceptions.RequestException as e:
        bot.send_message(CHAT_ID, f"🚨 Ошибка: {e}")
        return None, None, None

def write_to_file(data):
    with open(FILE_PATH, 'a') as file:
        file.write(data + '\n')

def send_file_via_telegram(file_path):
    with open(file_path, 'rb') as file:
        bot.send_document(CHAT_ID, file)

def check_file_size_and_send():
    file_size_mb = os.path.getsize(FILE_PATH) / (1024 * 1024)
    if file_size_mb >= MAX_FILE_SIZE_MB:
        bot.send_message(CHAT_ID, "📂 #почты")
        send_file_via_telegram(FILE_PATH)
        os.remove(FILE_PATH)

def main():
    domains = get_domains()
    if not domains:
        bot.send_message(CHAT_ID, "🚨 Не удалось получить домены. Завершение работы.")
        return

    count = 0
    request_count = 0

    while True:
        try:
            if count % 25 == 0 and count > 0:
                file_size = os.path.getsize(FILE_PATH) / (1024 * 1024)
                total_emails = count
                bot.send_message(CHAT_ID, f"🌟 Взято {total_emails} почт. Текущий размер файла: {file_size:.2f} MB 📁")

            domain = random.choice(domains)
            email, password, token = create_account_and_get_token(domain)
            if not email or not password or not token:
                continue
            write_to_file(f'{email}:{password}:{token}')

            # Информация в терминале
            print(f"Создана почта: {email}")
            print(f"Пароль: {password}")
            print(f"Токен: {token}")

            count += 1
            request_count += 1

            # Управление частотой запросов
            if request_count >= REQUEST_LIMIT:
                bot.send_message(CHAT_ID, "⏳ Достигнут лимит запросов, делаем паузу...")
                time.sleep(WAIT_TIME)  # Ожидание перед следующими запросами
                request_count = 0

            check_file_size_and_send()

            # Время ожидания от 10 до 25 секунд
            time.sleep(random.uniform(MIN_WAIT_TIME, MAX_WAIT_TIME))

        except requests.exceptions.RequestException as e:
            bot.send_message(CHAT_ID, f"🚨 Ошибка: {e}")
            time.sleep(5)  # Ожидание перед повтором в случае ошибки

if __name__ == '__main__':
    main()
