import telebot
from telebot import types
import json
import os
import re

API_TOKEN = '7024190964:AAEzgPV9RvoJMbBBShBvSo-K5yEIsq08D4I'
CHANNEL_ID = '@GameDevAssetsHub'
SUPPORT_BOT_LINK = 'https://t.me/your_support_bot'
TOKENS_FILE = 'tokens.json'
USERS_FILE = 'users.json'
ADMIN_ID = '6578018656'  # Ваш ID
LOG_CHANNEL_ID = '@GameDevAssetsHub'  # Канал для логирования

# Процент комиссии на вывод
WITHDRAWAL_FEE_PERCENT = 3

bot = telebot.TeleBot(API_TOKEN)

def load_data(file_name):
    if os.path.exists(file_name):
        with open(file_name, 'r') as file:
            return json.load(file)
    else:
        return {}

def save_data(file_name, data):
    with open(file_name, 'w') as file:
        json.dump(data, file, indent=4)

# Загрузим данные
tokens_data = load_data(TOKENS_FILE) or {}
users_data = load_data(USERS_FILE) or {}

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
    global tokens_data
    if not isinstance(tokens_data, dict):
        tokens_data = {}
    unique_tokens = [token for token in tokens if token not in tokens_data]
    if unique_tokens:
        users_data[user_id]['tokens'].extend(unique_tokens)
        users_data[user_id]['hold'] += 0.01 * len(unique_tokens)
        users_data[user_id]['total_tokens'] += len(unique_tokens)
        tokens_data.update({token: user_id for token in unique_tokens})
        save_data(USERS_FILE, users_data)
        save_data(TOKENS_FILE, tokens_data)
    return len(unique_tokens)

def approve_tokens(user_id, count):
    users_data[user_id]['balance'] += 0.01 * count
    users_data[user_id]['tokens'] = []
    save_data(USERS_FILE, users_data)

def reject_tokens(user_id, count):
    users_data[user_id]['hold'] -= 0.01 * count
    users_data[user_id]['tokens'] = []
    save_data(USERS_FILE, users_data)

def log_message(message):
    bot.send_message(LOG_CHANNEL_ID, message)

def main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📥 Загрузить токены"))
    markup.add(types.KeyboardButton("💼 Профиль"))
    markup.add(types.KeyboardButton("🆘 Тех. поддержка"))
    if user_id == ADMIN_ID:
        markup.add(types.KeyboardButton("🔧 Админка"))
    return markup

def back_to_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📥 Загрузить токены"))
    markup.add(types.KeyboardButton("💼 Профиль"))
    markup.add(types.KeyboardButton("🆘 Тех. поддержка"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    add_user(user_id)
    bot.send_message(user_id, "Привет! Выберите действие:", reply_markup=main_keyboard(user_id))

@bot.message_handler(func=lambda message: message.text == "📥 Загрузить токены")
def upload_tokens(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Через файл"))
    markup.add(types.KeyboardButton("Через бота"))
    markup.add(types.KeyboardButton("🔙 Назад"))
    bot.send_message(message.chat.id, "Как вы хотите загрузить токены?", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Через файл")
def upload_tokens_file(message):
    bot.send_message(message.chat.id, "Отправьте файл с токенами.")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == 'text/plain':
        user_id = str(message.chat.id)
        file_info = bot.get_file(message.document.file_id)
        file = bot.download_file(file_info.file_path)
        tokens = file.decode('utf-8').splitlines()
        count = add_tokens(user_id, tokens)
        if count > 0:
            bot.send_message(message.chat.id, f"Токены загружены. На проверке: {count} токенов. 💰 Ваш баланс будет обновлен после проверки.")
        else:
            bot.send_message(message.chat.id, "Все токены уже существуют.")
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=back_to_main_keyboard())
    else:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте текстовый файл (.txt).")

@bot.message_handler(func=lambda message: message.text == "Через бота")
def upload_tokens_via_bot(message):
    bot.send_message(message.chat.id, "Введите токены по одному (максимум 15). Когда закончите, введите 'Готово'.")
    bot.register_next_step_handler(message, collect_tokens, [])

def collect_tokens(message, tokens):
    if message.text.lower() == 'готово' or len(tokens) == 15:
        if tokens:
            count = add_tokens(str(message.chat.id), tokens)
            if count > 0:
                bot.send_message(message.chat.id, f"Токены загружены. На проверке: {count} токенов. 💰 Ваш баланс будет обновлен после проверки.")
            else:
                bot.send_message(message.chat.id, "Все токены уже существуют.")
        else:
            bot.send_message(message.chat.id, "Вы не ввели ни одного токена.")
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=back_to_main_keyboard())
    else:
        tokens.append(message.text)
        bot.send_message(message.chat.id, f"Токен {len(tokens)}/15 добавлен.")
        bot.register_next_step_handler(message, collect_tokens, tokens)

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
    balance = users_data.get(user_id, {}).get('balance', 0.0)
    if balance >= 5:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("🔙 Назад"))
        bot.send_message(call.message.chat.id, "Введите сумму для вывода (минимум 5 рублей):", reply_markup=markup)
        bot.register_next_step_handler(call.message, process_withdrawal_amount)
    else:
        bot.send_message(call.message.chat.id, "Сумма для вывода должна быть не меньше 5 рублей.")

def process_withdrawal_amount(message):
    user_id = str(message.chat.id)
    try:
        amount = float(message.text)
        if amount >= 5 and amount <= users_data.get(user_id, {}).get('balance', 0.0):
            # Рассчитываем комиссию
            fee = amount * (WITHDRAWAL_FEE_PERCENT / 100)
            net_amount = amount - fee

            # Убираем средства с баланса и не затрагиваем холд
            users_data[user_id]['balance'] -= amount
            save_data(USERS_FILE, users_data)
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("🔙 Назад"))
            bot.send_message(message.chat.id, f"Введите Payeer адрес для вывода {net_amount:.2f} рублей (с учетом комиссии {fee:.2f} рублей):", reply_markup=markup)
            bot.register_next_step_handler(message, process_payeer_address, net_amount, fee)
        else:
            bot.send_message(message.chat.id, "Введите корректную сумму (минимум 5 рублей).")
            bot.register_next_step_handler(message, process_withdrawal_amount)
    except ValueError:
        bot.send_message(message.chat.id, "Введите сумму числом.")
        bot.register_next_step_handler(message, process_withdrawal_amount)

def process_payeer_address(message, amount, fee):
    user_id = str(message.chat.id)
    payeer_address = message.text
    # Отправляем информацию в админ канал для проверки
    log_message(f"💸 Запрос на вывод средств\nID пользователя: {user_id}\nСумма: {amount:.2f} рублей\nКомиссия: {fee:.2f} рублей\nАдрес Payeer: {payeer_address}")
    bot.send_message(message.chat.id, "Ваш запрос на вывод средств отправлен на проверку. Мы свяжемся с вами в ближайшее время.")
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=main_keyboard(user_id))

@bot.message_handler(func=lambda message: message.text == "🆘 Тех. поддержка")
def support(message):
    bot.send_message(message.chat.id, f"Свяжитесь с нашей техподдержкой: {SUPPORT_BOT_LINK}")

@bot.message_handler(func=lambda message: message.text == "🔧 Админка")
def admin_panel(message):
    if str(message.chat.id) == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("📁 Проверка токенов"))
        markup.add(types.KeyboardButton("📋 Скачать все токены"))
        markup.add(types.KeyboardButton("🔙 Назад"))
        bot.send_message(message.chat.id, "Выберите действие в админке:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Вы не имеете доступа к админке.")

@bot.message_handler(func=lambda message: message.text == "📁 Проверка токенов")
def check_tokens(message):
    if str(message.chat.id) == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Скачать токены для проверки"))
        markup.add(types.KeyboardButton("🔙 Назад"))
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Скачать токены для проверки")
def download_tokens_for_check(message):
    if str(message.chat.id) == ADMIN_ID:
        # Создаем файл с токенами
        with open('tokens_for_check.txt', 'w') as file:
            for token, user_id in tokens_data.items():
                file.write(f"{token} - {user_id}\n")
        
        with open('tokens_for_check.txt', 'rb') as file:
            bot.send_document(message.chat.id, file)

@bot.message_handler(func=lambda message: message.text == "📋 Скачать все токены")
def download_all_tokens(message):
    if str(message.chat.id) == ADMIN_ID:
        with open('all_tokens.txt', 'w') as file:
            for token, user_id in tokens_data.items():
                file.write(f"{token}\n")
        
        with open('all_tokens.txt', 'rb') as file:
            bot.send_document(message.chat.id, file)

@bot.message_handler(func=lambda message: message.text == "🔙 Назад")
def back(message):
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=main_keyboard(message.chat.id))

bot.polling()
