import telebot
from telebot import types
import requests
import json
import os
import time

# Ваш токен бота
TOKEN = '7231579579:AAHAIYua8pOsNGkUGKxp6zK_JIB0pkq9PAA'
ADMIN_ID = 6578018656

bot = telebot.TeleBot(TOKEN)

# Создаем файл bot_tokens.json, если его нет
if not os.path.exists('bot_tokens.json'):
    with open('bot_tokens.json', 'w') as file:
        json.dump([], file)

# Функция для проверки статуса бота
def check_bot_status(bot_token):
    url = f'https://api.telegram.org/bot{bot_token}/getMe'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info['ok']:
                return bot_info['result']['username'], '🟢 Онлайн'
        return None, '🔴 Офлайн'
    except:
        return None, '🔴 Офлайн'

# Функция для перезапуска бота
def restart_bot():
    bot.send_message(ADMIN_ID, "⚠️ Бот отключается...")
    time.sleep(3)
    try:
        bot.polling(none_stop=True)
        bot.send_message(ADMIN_ID, "✅ Бот успешно запущен.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Бот не удалось запустить. Ошибка: {e}")

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_command(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("🟢 Боты онлайн")
        btn2 = types.KeyboardButton("🔴 Боты оффлайн")
        btn3 = types.KeyboardButton("📝 Все боты")
        btn4 = types.KeyboardButton("➕ Добавить бота")
        btn5 = types.KeyboardButton("➖ Удалить бота")
        markup.add(btn1, btn2, btn3, btn4, btn5)
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этому боту.")

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.from_user.id != ADMIN_ID:
        return

    if message.text == "🟢 Боты онлайн":
        show_online_bots(message)

    elif message.text == "🔴 Боты оффлайн":
        show_offline_bots(message)

    elif message.text == "📝 Все боты":
        show_all_bots(message)

    elif message.text == "➕ Добавить бота":
        bot.send_message(message.chat.id, "Отправьте токен бота, чтобы добавить его.")
        bot.register_next_step_handler(message, add_bot_token)

    elif message.text == "➖ Удалить бота":
        bot.send_message(message.chat.id, "Отправьте токен бота, чтобы удалить его.")
        bot.register_next_step_handler(message, delete_bot_token)

def show_online_bots(message):
    online_bots = []
    offline_bots = []

    with open('bot_tokens.json', 'r') as file:
        bot_tokens = json.load(file)

    for bot_token in bot_tokens:
        username, status = check_bot_status(bot_token)
        if status == '🟢 Онлайн':
            online_bots.append(f'@{username} - {status}')
        else:
            offline_bots.append(f'@{username if username else "Неизвестно"} - {status}')

    if online_bots:
        bot.send_message(message.chat.id, "\n".join(online_bots))
    else:
        bot.send_message(message.chat.id, "Нет ботов онлайн. 🟢")

def show_offline_bots(message):
    offline_bots = []

    with open('bot_tokens.json', 'r') as file:
        bot_tokens = json.load(file)

    for bot_token in bot_tokens:
        username, status = check_bot_status(bot_token)
        if status == '🔴 Офлайн':
            offline_bots.append(f'@{username if username else "Неизвестно"} - {status}')

    if offline_bots:
        bot.send_message(message.chat.id, "\n".join(offline_bots))
    else:
        bot.send_message(message.chat.id, "Нет ботов оффлайн. 🔴")

def show_all_bots(message):
    all_bots = []

    with open('bot_tokens.json', 'r') as file:
        bot_tokens = json.load(file)

    for bot_token in bot_tokens:
        username, status = check_bot_status(bot_token)
        all_bots.append(f'@{username if username else "Неизвестно"} - {status}')

    if all_bots:
        bot.send_message(message.chat.id, "\n".join(all_bots))
    else:
        bot.send_message(message.chat.id, "Нет добавленных ботов. 📝")

def add_bot_token(message):
    bot_token = message.text

    with open('bot_tokens.json', 'r') as file:
        bot_tokens = json.load(file)

    if bot_token in bot_tokens:
        bot.send_message(message.chat.id, "Этот бот уже добавлен.")
        return

    bot_tokens.append(bot_token)

    with open('bot_tokens.json', 'w') as file:
        json.dump(bot_tokens, file, indent=4)

    bot.send_message(message.chat.id, "Бот успешно добавлен. 🟢")

def delete_bot_token(message):
    bot_token = message.text

    with open('bot_tokens.json', 'r') as file:
        bot_tokens = json.load(file)

    if bot_token not in bot_tokens:
        bot.send_message(message.chat.id, "Этот бот не найден.")
        return

    bot_tokens.remove(bot_token)

    with open('bot_tokens.json', 'w') as file:
        json.dump(bot_tokens, file, indent=4)

    bot.send_message(message.chat.id, "Бот успешно удален. ➖")

# Запуск бота с обработкой возможного отключения
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        bot.send_message(ADMIN_ID, "⚠️ Бот отключился. Пытаюсь перезапустить...")
        time.sleep(5)  # Ожидание перед повторным запуском
        try:
            bot.polling(none_stop=True)
            bot.send_message(ADMIN_ID, "✅ Бот успешно запущен.")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ Бот не удалось запустить. Ошибка: {e}")
            break
