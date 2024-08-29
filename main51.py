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

# Инициализация бота
bot = TeleBot(TELEGRAM_BOT_TOKEN)

def generate_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

def generate_email(domain):
    username = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return f'{username}@{domain}'

def get_domains():
    response = requests.get(f'{API_BASE_URL}/domains')
    response.raise_for_status()
    domains = response.json()["hydra:member"]
    return [domain["domain"] for domain in domains]

def create_account(domain):
    email = generate_email(domain)
    password = generate_password()
    account_data = {
        "address": email,
        "password": password
    }
    response = requests.post(f'{API_BASE_URL}/accounts', json=account_data)
    response.raise_for_status()
    account_info = response.json()
    account_id = account_info.get('id')
    return email, password, account_id

def get_token(email, password):
    token_data = {
        "address": email,
        "password": password
    }
    response = requests.post(f'{API_BASE_URL}/token', json=token_data)
    response.raise_for_status()
    token_info = response.json()
    return token_info.get('token')

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
    count = 0

    while True:
        try:
            if count % 25 == 0 and count > 0:
                file_size = os.path.getsize(FILE_PATH) / (1024 * 1024)
                total_emails = count
                bot.send_message(CHAT_ID, f"🌟 Взято {total_emails} почт. Текущий размер файла: {file_size:.2f} MB 📁")

            domain = random.choice(domains)
            email, password, account_id = create_account(domain)
            token = get_token(email, password)
            write_to_file(f'{email}:{password}:{token}')

            # Информация в терминале
            print(f"Создана почта: {email}")
            print(f"Пароль: {password}")
            print(f"Токен: {token}")

            count += 1

            check_file_size_and_send()

            # Время ожидания от 3 до 9 секунд
            time.sleep(random.uniform(3, 9))

        except requests.exceptions.RequestException as e:
            print(f"Ошибка: {e}")
            time.sleep(5)  # Ожидание перед повтором в случае ошибки

if __name__ == '__main__':
    main()
