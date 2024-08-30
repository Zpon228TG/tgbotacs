import requests
import telebot
import os
import time
import random
import string

# Укажите ваш токен бота и ID чата
TELEGRAM_BOT_TOKEN = '7426380650:AAEkJp4_EF4h8ZvLxBbNNWT8xXg7jRQ02n0'
CHAT_ID = '7412395676'

# Путь к файлу
FILE_PATH = 'emails.txt'
MAX_FILE_SIZE_MB = 9

# Создаем бота
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def log_message(message):
    """Функция для отправки сообщения в Telegram"""
    bot.send_message(CHAT_ID, message)

def generate_random_string(length=8):
    """Генерация случайной строки"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def generate_password(length=12):
    """Генерация случайного пароля"""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))

def create_email():
    """Функция для создания почты и получения токена"""
    # Получение списка доменов
    domain_response = requests.get('https://api.mail.tm/domains')
    if domain_response.status_code != 200:
        log_message(f'Ошибка при получении доменов: {domain_response.status_code}')
        return None, None, None
    
    domain_data = domain_response.json()
    if not domain_data.get('hydra:member'):
        log_message('Ошибка: Список доменов пуст')
        return None, None, None
    
    domain = domain_data['hydra:member'][0]['domain']
    email_address = f"{generate_random_string()}@{domain}"
    email_password = generate_password()

    # Создание аккаунта
    create_response = requests.post('https://api.mail.tm/accounts', json={
        'address': email_address,
        'password': email_password
    })
    if create_response.status_code != 201:
        log_message(f'Ошибка при создании аккаунта: {create_response.status_code} - {create_response.text}')
        return None, None, None

    # Получение токена
    token_response = requests.post('https://api.mail.tm/token', json={
        'address': email_address,
        'password': email_password
    })
    if token_response.status_code != 201:
        log_message(f'Ошибка при получении токена: {token_response.status_code}')
        return None, None, None
    
    email_token = token_response.json().get('token')
    return email_address, email_password, email_token

def main():
    """Основная функция для управления процессом создания почт и записи в файл"""
    log_message('Скрипт запущен')

    while True:
        email_address, email_password, email_token = create_email()
        if email_address and email_password and email_token:
            with open(FILE_PATH, 'a') as file:
                file.write(f'{email_address}:{email_password}:{email_token}\n')
            
            # Проверка размера файла
            if os.path.getsize(FILE_PATH) >= MAX_FILE_SIZE_MB * 1024 * 1024:  # 9 МБ
                bot.send_document(CHAT_ID, open(FILE_PATH, 'rb'))
                open(FILE_PATH, 'w').close()  # Очистка файла после отправки
                log_message(f'Файл отправлен. Размер файла достиг {MAX_FILE_SIZE_MB} МБ.')
        else:
            log_message('Не удалось создать почту')

        # Задержка между запросами
        time.sleep(3)

if __name__ == "__main__":
    main()
