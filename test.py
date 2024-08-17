import telebot
from telebot import types
import json
import os

API_TOKEN = '7024190964:AAEzgPV9RvoJMbBBShBvSo-K5yEIsq08D4I'
CHANNEL_ID = '@GameDevAssetsHub'
SUPPORT_BOT_LINK = 'https://t.me/your_support_bot'
TOKENS_FILE = 'tokens.json'
USERS_FILE = 'users.json'

bot = telebot.TeleBot(API_TOKEN)

# Функции для работы с файлами
def load_data(file_name):
    if os.path.exists(file_name):
        with open(file_name, 'r') as file:
            return json.load(file)
    else:
        return {}

def save_data(file_name, data):
    with open(file_name, 'w') as file:
        json.dump(data, file, indent=4)

# Инициализация данных
tokens_data = load_data(TOKENS_FILE)
users_data = load_data(USERS_FILE)

def add_user(user_id):
    if user_id not in users_data:
        users_data[user_id] = {
            'balance': 0.0,
            'tokens': [],
            'hold': 0.0,
            'total_tokens': 0
        }
        save_data(USERS_FILE, users_data)

def add_tokens(user_id, tokens):
    users_data[user_id]['tokens'].extend(tokens)
    users_data[user_id]['hold'] += 0.01 * len(tokens)
    users_data[user_id]['total_tokens'] += len(tokens)
    save_data(USERS_FILE, users_data)

def approve_tokens(user_id, count):
    users_data[user_id]['balance'] += 0.01 * count
    users_data[user_id]['hold'] -= 0.01 * count
    save_data(USERS_FILE, users_data)

def reject_tokens(user_id, count):
    users_data[user_id]['hold'] -= 0.01 * count
    save_data(USERS_FILE, users_data)

# Клавиатура для пользователя
def main_keyboard(is_admin=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📥 Загрузить токены")
    markup.add("💼 Профиль")
    markup.add("🆘 Тех. поддержка")
    if is_admin:
        markup.add("🔧 Админка")
    return markup

# Обработчики команд
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    is_admin = user_id == 'YOUR_ADMIN_ID'
    add_user(user_id)
    bot.send_message(user_id, "Привет! Выберите действие:", reply_markup=main_keyboard(is_admin))

@bot.message_handler(func=lambda message: message.text == "📥 Загрузить токены")
def upload_tokens(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Через файл", "Через бота")
    markup.add("🔙 Назад")
    bot.send_message(message.chat.id, "Как вы хотите загрузить токены?", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Через файл")
def upload_tokens_file(message):
    bot.send_message(message.chat.id, "Отправьте файл с токенами (максимум 5 штук).")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == 'text/plain':
        user_id = str(message.chat.id)
        file_info = bot.get_file(message.document.file_id)
        file = bot.download_file(file_info.file_path)
        tokens = file.decode('utf-8').splitlines()[:5]
        add_tokens(user_id, tokens)
        bot.send_message(user_id, f"Токены загружены. На проверке: {len(tokens)} токенов. 💰 Ваш баланс будет обновлен после проверки.")
    else:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте текстовый файл (.txt).")

@bot.message_handler(func=lambda message: message.text == "💼 Профиль")
def profile(message):
    user_id = str(message.chat.id)
    user_data = users_data.get(user_id, {})
    balance = user_data.get('balance', 0.0)
    hold = user_data.get('hold', 0.0)
    total_tokens = user_data.get('total_tokens', 0)
    
    profile_text = (
        f"🆔 Ваш ID: {user_id}\n"
        f"💰 Баланс: {balance:.2f} рублей\n"
        f"🪙 Всего токенов загружено: {total_tokens}\n"
        f"🔒 Сумма в холде: {hold:.2f} рублей"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💸 Вывести деньги", callback_data="withdraw"))
    bot.send_message(message.chat.id, profile_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "withdraw")
def withdraw_money(call):
    user_id = str(call.message.chat.id)
    balance = users_data[user_id]['balance']
    if balance >= 5:
        bot.send_message(call.message.chat.id, "Введите Payeer адрес:")
        bot.register_next_step_handler(call.message, process_payeer_address)
    else:
        bot.send_message(call.message.chat.id, "Сумма для вывода должна быть не меньше 5 рублей.")

def process_payeer_address(message):
    payeer_address = message.text
    user_id = str(message.chat.id)
    balance = users_data[user_id]['balance']
    bot.send_message(message.chat.id, f"Вы хотите вывести {balance:.2f} рублей на адрес {payeer_address}? (да/нет)")
    bot.register_next_step_handler(message, confirm_withdrawal, payeer_address, balance)

def confirm_withdrawal(message, payeer_address, balance):
    if message.text.lower() == "да":
        bot.send_message(message.chat.id, "Ваш запрос отправлен на обработку.")
        bot.send_message(
            CHANNEL_ID, 
            f"💰 Запрос на вывод средств:\n\n"
            f"🆔 ID: {message.chat.id}\n"
            f"💸 Сумма: {balance:.2f} рублей\n"
            f"📤 Payeer: {payeer_address}"
        )
        users_data[str(message.chat.id)]['balance'] = 0.0
        save_data(USERS_FILE, users_data)
    else:
        bot.send_message(message.chat.id, "Вывод отменен.")

@bot.message_handler(func=lambda message: message.text == "🆘 Тех. поддержка")
def support(message):
    bot.send_message(message.chat.id, f"Связаться с тех. поддержкой: {SUPPORT_BOT_LINK}")

# Админка
@bot.message_handler(func=lambda message: message.text == "🔧 Админка" and str(message.chat.id) == 'YOUR_ADMIN_ID')
def admin_panel(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Проверить токены", "Скачать все токены")
    markup.add("🔙 Назад")
    bot.send_message(message.chat.id, "Админка", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Проверить токены" and str(message.chat.id) == 'YOUR_ADMIN_ID')
def review_tokens(message):
    pending_users = [uid for uid in users_data if users_data[uid]['hold'] > 0]
    if pending_users:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for uid in pending_users:
            markup.add(uid)
        markup.add("🔙 Назад")
        bot.send_message(message.chat.id, "Выберите ID пользователя для проверки:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Нет токенов на проверке.")

@bot.message_handler(func=lambda message: message.text in users_data and str(message.chat.id) == 'YOUR_ADMIN_ID')
def review_user_tokens(message):
    user_id = message.text
    tokens = users_data[user_id]['tokens']
    tokens_text = '\n'.join(tokens)
    with open(f"{user_id}_tokens.txt", 'w') as file:
        file.write(tokens_text)
    with open(f"{user_id}_tokens.txt", 'rb') as file:
        bot.send_document(message.chat.id, file)
    os.remove(f"{user_id}_tokens.txt")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Все токены подходят", "Не все подходят")
    markup.add("🔙 Назад")
    bot.send_message(message.chat.id, "Итог проверки:", reply_markup=markup)
    bot.register_next_step_handler(message, finalize_review, user_id)

def finalize_review(message, user_id):
    if message.text == "Все токены подходят":
        approve_tokens(user_id, len(users_data[user_id]['tokens']))
        bot.send_message(message.chat.id, "Баланс пользователя обновлен.")
    elif message.text == "Не все подходят":
        bot.send_message(message.chat.id, "Введите количество подходящих токенов:")
        bot.register_next_step_handler(message, partial_approve_tokens, user_id)
    else:
        bot.send_message(message.chat.id, "Отмена проверки.")

def partial_approve_tokens(message, user_id):
    try:
        count = int(message.text)
        approve_tokens(user_id, count)
        reject_tokens(user_id, len(users_data[user_id]['tokens']) - count)
        bot.send_message(message.chat.id, "Баланс пользователя обновлен.")
    except ValueError:
        bot.send_message(message.chat.id, "Некорректное количество токенов.")

@bot.message_handler(func=lambda message: message.text == "Скачать все токены" and str(message.chat.id) == 'YOUR_ADMIN_ID')
def download_all_tokens(message):
    all_tokens = [token for uid in users_data for token in users_data[uid]['tokens']]
    tokens_text = '\n'.join(all_tokens)
    with open("all_tokens.txt", 'w') as file:
        file.write(tokens_text)
    with open("all_tokens.txt", 'rb') as file:
        bot.send_document(message.chat.id, file)
    os.remove("all_tokens.txt")

bot.polling()
