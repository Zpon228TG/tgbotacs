import requests
import time
import os
import telebot

# Настройки
api_base_url = 'https://api.mail.tm'
telegram_token = '7426380650:AAEkJp4_EF4h8ZvLxBbNNWT8xXg7jRQ02n0'  # Замените на ваш токен бота
chat_id = '7412395676'  # Замените на ваш чат ID
filename = 'emails.txt'
file_size_limit = 9 * 1024 * 1024  # 9 MB

bot = telebot.TeleBot(telegram_token)

def get_domains():
    response = requests.get(f'{api_base_url}/domains')
    response.raise_for_status()
    return response.json()['hydra:member']

def create_account(domain):
    email = f'user{int(time.time())}@{domain["domain"]}'
    password = 'password123'
    account_data = {
        "address": email,
        "password": password
    }
    response = requests.post(f'{api_base_url}/accounts', json=account_data)
    response.raise_for_status()
    return email, password

def get_token(email, password):
    token_data = {
        "address": email,
        "password": password
    }
    response = requests.post(f'{api_base_url}/token', json=token_data)
    response.raise_for_status()
    return response.json()['token']

def save_email_to_file(email, password, token):
    with open(filename, 'a') as file:
        file.write(f'{email}:{password}:{token}\n')

def send_file():
    with open(filename, 'rb') as file:
        bot.send_document(chat_id, file)

def main():
    while True:
        try:
            domains = get_domains()
            email, password = create_account(domains[0])
            token = get_token(email, password)
            save_email_to_file(email, password, token)
            if os.path.getsize(filename) >= file_size_limit:
                send_file()
                os.remove(filename)
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(3)

if __name__ == "__main__":
    main()
