import requests
import random
import string
import time
import os
import telebot

# Конфигурация Telegram-бота
TELEGRAM_TOKEN = '7426380650:AAEkJp4_EF4h8ZvLxBbNNWT8xXg7jRQ02n0'
CHAT_ID = '7412395676'
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# URL API
BASE_URL = "https://api.mail.tm"

# Функция для генерации случайной строки
def generate_random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Функция для получения доменов
def get_domains():
    response = requests.get(f"{BASE_URL}/domains")
    response.raise_for_status()
    return response.json()['hydra:member']

# Функция для создания аккаунта
def create_account(domain, token):
    email = generate_random_string(10) + "@" + domain
    password = generate_random_string(10)
    response = requests.post(
        f"{BASE_URL}/accounts",
        headers={"Authorization": f"Bearer {token}"},
        json={"address": email, "password": password}
    )
    response.raise_for_status()
    return email, password, response.json()['id']

# Функция для получения токена
def get_token(address, password):
    try:
        response = requests.post(
            f"{BASE_URL}/token",
            json={"address": address, "password": password}
        )
        response.raise_for_status()
        return response.json()['token']
    except requests.exceptions.RequestException as e:
        # Печать полного ответа для диагностики
        print(f"Ошибка при получении токена: {e}")
        if e.response:
            print(f"Ответ от сервера: {e.response.text}")
        send_telegram_message(f"Ошибка при получении токена: {e}\nОтвет от сервера: {e.response.text if e.response else 'Нет ответа'}")
        raise

# Функция для получения сообщений
def get_messages(token):
    response = requests.get(
        f"{BASE_URL}/messages",
        headers={"Authorization": f"Bearer {token}"}
    )
    response.raise_for_status()
    return response.json()['hydra:member']

# Функция для отправки сообщения в Telegram
def send_telegram_message(text):
    try:
        bot.send_message(chat_id=CHAT_ID, text=text)
    except Exception as e:
        print(f"Ошибка при отправке сообщения в Telegram: {e}")

# Основная функция
def main():
    domains = get_domains()
    domain = domains[0]['domain']  # Выберите первый домен
    
    # Получите токен для существующего аккаунта
    address = "existing@example.com"
    password = "existing_password"
    
    try:
        token = get_token(address, password)
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при получении токена: {e}")
        send_telegram_message(f"Ошибка при получении токена: {e}")
        return

    file_path = "accounts.txt"
    max_file_size_mb = 9

    # Генерация и создание нового аккаунта
    while True:
        try:
            email, password, account_id = create_account(domain, token)
            print(f"Создан новый аккаунт: {email}, {password}, ID: {account_id}")

            # Задержка для предотвращения ошибок из-за частых запросов
            time.sleep(random.uniform(10, 25))

            # Получите список сообщений для проверки
            messages = get_messages(token)
            print(f"Получено сообщений: {len(messages)}")

            # Запись данных в файл
            with open(file_path, "a") as file:
                file.write(f"{email}:{password}:{token}\n")

            # Проверка размера файла и отправка в Telegram
            if os.path.getsize(file_path) > max_file_size_mb * 1024 * 1024:
                send_telegram_message(f"#почты Файл превышает {max_file_size_mb} МБ, отправляю...")
                with open(file_path, "rb") as file:
                    bot.send_document(chat_id=CHAT_ID, document=file)
                os.remove(file_path)

            # Уведомление о добавлении почты
            send_telegram_message(f"Взял 1 почту. Размер файла: {os.path.getsize(file_path) / (1024 * 1024):.2f} МБ")

            # Запуск функции через 10-25 секунд
            time.sleep(random.uniform(10, 25))
        
        except requests.exceptions.HTTPError as err:
            # Обработка ошибок
            if err.response.status_code == 429:
                print("🚨 Слишком много запросов, делаем паузу...")
                send_telegram_message("🚨 Слишком много запросов, делаем паузу...")
                time.sleep(60)  # Пауза 1 минута
            elif err.response.status_code == 401:
                print("🚨 Ошибка авторизации. Проверьте токен.")
                send_telegram_message("🚨 Ошибка авторизации. Проверьте токен.")
                break
            else:
                print(f"🚨 Ошибка: {err}")
                send_telegram_message(f"🚨 Ошибка: {err}")
                time.sleep(60)  # Пауза 1 минута

if __name__ == "__main__":
    main()
