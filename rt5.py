import requests
import telebot
import json
import os
import time

# Укажите ваш токен бота и ID чата
TELEGRAM_BOT_TOKEN = '7426380650:AAEkJp4_EF4h8ZvLxBbNNWT8xXg7jRQ02n0'
CHAT_ID = '7412395676'

# Путь к файлу
FILE_PATH = 'emails.txt'
MAX_EMAILS = 2500

# Создайте бота
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def log_message(message):
    bot.send_message(CHAT_ID, message)

def create_email():
    response = requests.get('https://api.mail.tm/domains')
    domains = response.json().get('hydra:member', [])
    domain = domains[0]['domain'] if domains else None

    if domain:
        address = f'user@{domain}'
        password = 'password'  # Используйте безопасный метод генерации паролей
        response = requests.post('https://api.mail.tm/accounts', json={
            'address': address,
            'password': password
        })
        account = response.json()
        token_response = requests.post('https://api.mail.tm/token', json={
            'address': address,
            'password': password
        })
        token = token_response.json().get('token')
        return address, password, token
    return None, None, None

def main():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, 'r') as file:
            lines = file.readlines()
            if len(lines) >= MAX_EMAILS:
                bot.send_document(CHAT_ID, open(FILE_PATH, 'rb'))
                open(FILE_PATH, 'w').close()  # Очистите файл после отправки
                log_message(f"Файл отправлен, размер файла: {os.path.getsize(FILE_PATH) / (1024 * 1024):.2f} МБ")
                return
    else:
        open(FILE_PATH, 'w').close()  # Создайте файл, если он не существует

    log_message('Скрипт запущен')

    while True:
        address, password, token = create_email()
        if address:
            with open(FILE_PATH, 'a') as file:
                file.write(f'{address}:{password}:{token}\n')
            if os.path.getsize(FILE_PATH) >= 9 * 1024 * 1024:  # 9 MB
                bot.send_document(CHAT_ID, open(FILE_PATH, 'rb'))
                open(FILE_PATH, 'w').close()  # Очистите файл после отправки
                log_message(f"Файл отправлен, размер файла: {os.path.getsize(FILE_PATH) / (1024 * 1024):.2f} МБ")
        time.sleep(3)

if __name__ == "__main__":
    main()
