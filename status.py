import requests
import telebot
from telebot import types
import time
import os
import json

# Токен вашего бота и ваш Telegram ID
TOKEN = '7359279162:AAGjFuIZaCxp1TvsY8vVyw5ryah3vTPXTm4'
ADMIN_ID = 6578018656

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Функция для проверки статуса бота через отправку команды
def check_bot_status(bot_token):
    try:
        # Отправляем тестовое сообщение другому боту
        test_message = {"chat_id": ADMIN_ID, "text": "/start"}
        response = requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', data=test_message)
        
        # Проверяем, удалось ли отправить сообщение
        if response.status_code == 200 and response.json().get("ok"):
            return 'online'
        else:
            return 'offline'
    except requests.RequestException:
        return 'offline'

# Главное меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_online = types.KeyboardButton("🟢 Боты онлайн")
    btn_offline = types.KeyboardButton("🔴 Боты офлайн")
    btn_all = types.KeyboardButton("🔍 Все боты")
    btn_add = types.KeyboardButton("➕ Добавить бота")
    btn_remove = types.KeyboardButton("❌ Удалить бота")
    markup.add(btn_online, btn_offline, btn_all, btn_add, btn_remove)
    return markup

# Обработка команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "Извините, этот бот доступен только для администратора.")
        return
    bot.reply_to(message, "👋 Привет! Выберите действие:", reply_markup=main_menu())

# Обработка нажатий на кнопки
@bot.message_handler(func=lambda message: True)
def menu_handler(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "Извините, этот бот доступен только для администратора.")
        return

    if message.text == "🟢 Боты онлайн":
        show_online_bots(message)
    elif message.text == "🔴 Боты офлайн":
        show_offline_bots(message)
    elif message.text == "🔍 Все боты":
        show_all_bots(message)
    elif message.text == "➕ Добавить бота":
        add_bot(message)
    elif message.text == "❌ Удалить бота":
        remove_bot(message)
    else:
        bot.reply_to(message, "❓ Пожалуйста, выберите действие из меню.", reply_markup=main_menu())

def show_online_bots(message):
    bots = load_data('bots.json')
    online_bots = [bot_token for bot_token, status in bots.items() if status == 'online']
    if not online_bots:
        bot.reply_to(message, "🟢 Нет онлайн ботов.")
    else:
        bot.reply_to(message, "🟢 Онлайн боты:\n" + "\n".join(online_bots))

def show_offline_bots(message):
    bots = load_data('bots.json')
    offline_bots = [bot_token for bot_token, status in bots.items() if status == 'offline']
    if not offline_bots:
        bot.reply_to(message, "🔴 Нет оффлайн ботов.")
    else:
        bot.reply_to(message, "🔴 Оффлайн боты:\n" + "\n".join(offline_bots))

def show_all_bots(message):
    bots = load_data('bots.json')
    response = "\n".join([f"Токен: {bot_token}, Статус: {status}" for bot_token, status in bots.items()])
    bot.reply_to(message, response if response else "🔍 Нет зарегистрированных ботов.")

def add_bot(message):
    msg = bot.reply_to(message, "✍️ Введите токен бота для добавления:")
    bot.register_next_step_handler(msg, process_add_bot)

def process_add_bot(message):
    bot_token = message.text
    if not check_bot_status(bot_token):
        bot.reply_to(message, "❌ Бот не отвечает на команды. Проверьте токен.")
        return

    bots = load_data('bots.json')
    bots[bot_token] = 'online'
    save_data('bots.json', bots)
    bot.reply_to(message, "✅ Бот добавлен и отмечен как онлайн.")

def remove_bot(message):
    msg = bot.reply_to(message, "✍️ Введите токен бота для удаления:")
    bot.register_next_step_handler(msg, process_remove_bot)

def process_remove_bot(message):
    bot_token = message.text
    bots = load_data('bots.json')
    if bot_token in bots:
        del bots[bot_token]
        save_data('bots.json', bots)
        bot.reply_to(message, "✅ Бот удален.")
    else:
        bot.reply_to(message, "❌ Бот с таким токеном не найден.")

def load_data(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, 'r') as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return {}  # Если файл пуст или некорректен, возвращаем пустой словарь

def save_data(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

# Основной цикл обработки сообщений
while True:
    try:
        bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
    except Exception as e:
        error_message = f"Ошибка: {e}"
        print(error_message)
        try:
            bot.send_message(ADMIN_ID, error_message)  # Отправка сообщения об ошибке администратору
        except Exception as send_error:
            print(f"Ошибка при отправке сообщения: {send_error}")
        time.sleep(15)
