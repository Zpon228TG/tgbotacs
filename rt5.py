import telebot
import pymailtm
import json
import os

# Telegram bot setup
TELEGRAM_BOT_TOKEN = '7426380650:AAEkJp4_EF4h8ZvLxBbNNWT8xXg7jRQ02n0'
CHAT_ID = '7412395676'
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# File setup
FILE_PATH = 'emails.txt'
EMAIL_LIMIT = 2500
EMAIL_NOTIFICATION_LIMIT = 15

# Counter for emails
email_count = 0

def send_telegram_message(message):
    bot.send_message(CHAT_ID, message)

def send_telegram_file():
    with open(FILE_PATH, 'rb') as f:
        bot.send_document(CHAT_ID, f)
    os.remove(FILE_PATH)

def generate_email_data():
    global email_count
    domain = pymailtm.get_domain()
    email_address = pymailtm.gen_address(domain)
    password = pymailtm.gen_password()
    
    try:
        account = pymailtm.Account(email=email_address, password=password)
        token = account.token
    except pymailtm.PyMailTMException as e:
        print(f"Ошибка при создании аккаунта: {e}")
        return None
    
    if token:
        email_data = f"{email_address}:{password}:{token}"
        with open(FILE_PATH, 'a') as f:
            f.write(email_data + '\n')
        
        email_count += 1
        
        if email_count % EMAIL_NOTIFICATION_LIMIT == 0:
            send_telegram_message(f"📧 Взял {email_count} почт!")

        if email_count >= EMAIL_LIMIT:
            send_telegram_message("📁 Достигнут лимит в 2500 почт. Отправляю файл.")
            send_telegram_file()
            email_count = 0
    else:
        print("Ошибка при получении токена")
        return None

def main():
    while True:
        generate_email_data()

if __name__ == "__main__":
    main()
