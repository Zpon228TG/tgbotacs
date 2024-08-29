import requests
import json
import time
import os
from telebot import TeleBot

# Настройки
TELEGRAM_BOT_TOKEN = '7426380650:AAEkJp4_EF4h8ZvLxBbNNWT8xXg7jRQ02n0'
CHAT_ID = '7412395676'
FILE_PATH = 'emails.txt'
MAX_FILE_SIZE_MB = 9
API_BASE_URL = 'https://api.mail.tm'

# Инициализация бота
bot = TeleBot(TELEGRAM_BOT_TOKEN)

def get_domains():
    response = requests.get(f'{API_BASE_URL}/domains')
    response.raise_for_status()
    domains = response.json()["hydra:member"]
    return [domain["domain"] for domain in domains]

def create_account(domain):
    """Создание аккаунта и получение email, пароля и токена"""
    account_data = {
        "address": f'test_{int(time.time())}@{domain}',
        "password": "Password123"  # Здесь может быть любой пароль, но его вернёт API
    }
    response = requests.post(f'{API_BASE_URL}/accounts', json=account_data)
    response.raise_for_status()
    
    account_info = response.json()
    email = account_info['address']
    password = account_info['password']  # Пароль, который был передан в запросе
    token = account_info['id']  # Токен, который вернул API
    
    return email, password, token

def write_to_file(data):
    with open(FILE_PATH, 'a') as file:
        file.write(data + '\n')

def send_file_via_telegram(file_path):
    with open(file_path, 'rb') as file:
        bot.send_message(CHAT_ID, "#почты 📧", disable_notification=True)
        bot.send_document(CHAT_ID, file)

def check_file_size_and_send():
    file_size_mb = os.path.getsize(FILE_PATH) / (1024 * 1024)
    if file_size_mb >= MAX_FILE_SIZE_MB:
        send_file_via_telegram(FILE_PATH)
        os.remove(FILE_PATH)

def main():
    domains = get_domains()
    count = 0

    while True:
        try:
            if count % 5 == 0 and count > 0:
                file_size = os.path.getsize(FILE_PATH) / (1024 * 1024)
                total_emails = count
                bot.send_message(CHAT_ID, f"📩 Взял {total_emails} почт\n💾 Размер файла: {file_size:.2f} MB\n📊 Всего почт: {total_emails}")

            domain = domains[count % len(domains)]
            email, password, token = create_account(domain)
            write_to_file(f'{email}:{password}:{token}')

            count += 1

            check_file_size_and_send()
            time.sleep(3)

        except requests.exceptions.RequestException as e:
            print(f"Ошибка: {e}")
            time.sleep(5)  # Ожидание перед повтором в случае ошибки

if __name__ == '__main__':
    main()
