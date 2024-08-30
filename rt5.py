import time
import os
import requests
from pymailtm import MailTm
import telebot

# Настройки Telegram
TELEGRAM_TOKEN = '7426380650:AAEkJp4_EF4h8ZvLxBbNNWT8xXg7jRQ02n0'
CHAT_ID = '7412395676'
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Настройки Temp Mail
MAILTM_API_KEY = 'your_mailtm_api_key'
mailtm = MailTm()  # Попробуйте инициализировать без аргументов

def send_file_to_telegram(file_path):
    with open(file_path, 'rb') as file:
        bot.send_document(chat_id=CHAT_ID, document=file, caption='#почты')

def notify_user(message):
    bot.send_message(chat_id=CHAT_ID, text=message)

def get_new_email():
    response = mailtm.create_mail()  # Обновите метод, если он другой
    return response

def main():
    email_records = []
    
    while True:
        email = get_new_email()
        email_records.append(f"{email['email']}:{email['password']}:{email['token']}\n")

        # Запись в файл и отправка, если достигнут лимит
        if len(email_records) >= MAX_RECORDS or (os.path.exists(FILE_PATH) and os.path.getsize(FILE_PATH) / (1024 * 1024) >= MAX_FILE_SIZE_MB):
            with open(FILE_PATH, 'a') as file:
                file.writelines(email_records)
            
            # Отправка файла и очистка данных
            send_file_to_telegram(FILE_PATH)
            email_records = []
            if os.path.exists(FILE_PATH):
                os.remove(FILE_PATH)
            
            # Отправка уведомления
            notify_user(f"Файл с почтами отправлен. Всего почт: {len(email_records)}")

        # Периодическая задержка
        time.sleep(3)

if __name__ == "__main__":
    main()
