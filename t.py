import telebot
from telebot import types
import json
import os

API_TOKEN = '7024190964:AAEzgPV9RvoJMbBBShBvSo-K5yEIsq08D4I'
CHANNEL_ID = '@GameDevAssetsHub'
SUPPORT_BOT_LINK = 'https://t.me/your_support_bot'
TOKENS_FILE = 'tokens.json'
USERS_FILE = 'users.json'
ADMIN_ID = '6578018656'  # Ваш ID
LOG_CHANNEL_ID = '@log_channel'  # Канал для логирования

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

tokens_data = load_data(TOKENS_FILE)
users_data = load_data(USERS_FILE)

def log_message(message):
    bot.send_message(LOG_CHANNEL_ID, message)

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
    unique_tokens = [token for token in tokens if token not in tokens_data]
    if unique_tokens:
        users_data[user_id]['tokens'].extend(unique_tokens)
        users_data[user_id]['hold'] += 0.01 * len(unique_tokens)
        users_data[user_id]['total_tokens'] += len(unique_tokens)
        tokens_data.update({token: user_id for token in unique_tokens})
        save_data(USERS_FILE, users_data)
        save_data(TOKENS_FILE, tokens_data)
        log_message(f"Добавлены токены для пользователя {user_id}: {len(unique_tokens)} токенов.")
    return len(unique_tokens)

def approve_tokens(user_id, count):
    users_data[user_id]['balance'] += 0.01 * count
    users_data[user_id]['hold'] -= 0.01 * count
    users_data[user_id]['tokens'] = []
    save_data(USERS_FILE, users_data)
    log_message(f"Одобрены {count} токенов для пользователя {user_id}.")

def reject_tokens(user_id, count):
    users_data[user_id]['hold'] -= 0.01 * count
    users_data[user_id]['tokens'] = []
    save_data(USERS_FILE, users_data)
    log_message(f"Отклонены {count} токенов для пользователя {user_id}.")

def main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📥 Загрузить токены")
    markup.add("💼 Профиль")
    markup.add("🆘 Тех. поддержка")
    if user_id == ADMIN_ID:
        markup.add("🔧 Админка")
    return markup

def back_to_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📥 Загрузить токены")
    markup.add("💼 Профиль")
    markup.add("🆘 Тех. поддержка")
    return markup

def back_to_admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔧 Админка")
    markup.add("🔙 Назад")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    add_user(user_id)
    bot.send_message(user_id, "Привет! Выберите действие:", reply_markup=main_keyboard(user_id))

@bot.message_handler(func=lambda message: message.text == "📥 Загрузить токены")
def upload_tokens(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Через файл", "Через бота")
    markup.add("🔙 Назад")
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
        markup.add("🔙 Назад")
        bot.send_message(call.message.chat.id, "Введите сумму для вывода (минимум 5 рублей):", reply_markup=markup)
        bot.register_next_step_handler(call.message, process_withdrawal_amount)
    else:
        bot.send_message(call.message.chat.id, "Сумма для вывода должна быть не меньше 5 рублей.")

def process_withdrawal_amount(message):
    user_id = str(message.chat.id)
    try:
        amount = float(message.text)
        if amount >= 5 and amount <= users_data.get(user_id, {}).get('balance', 0.0):
            users_data[user_id]['balance'] -= amount
            save_data(USERS_FILE, users_data)

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("🔙 Назад")
            bot.send_message(message.chat.id, f"Введите Payeer адрес для вывода {amount:.2f} рублей:", reply_markup=markup)
            bot.register_next_step_handler(message, process_payeer_address, amount)
        else:
            bot.send_message(message.chat.id, "Введите корректную сумму (минимум 5 рублей и не больше вашего баланса).")
            bot.register_next_step_handler(message, process_withdrawal_amount)
    except ValueError:
        bot.send_message(message.chat.id, "Введите корректное число.")
        bot.register_next_step_handler(message, process_withdrawal_amount)

def process_payeer_address(message, amount):
    user_id = str(message.chat.id)
    payeer_address = message.text
    if payeer_address:
        bot.send_message(
            CHANNEL_ID,
            f"💵 Запрос на вывод средств\n"
            f"🆔 ID пользователя: {user_id}\n"
            f"💰 Сумма: {amount:.2f} рублей\n"
            f"📧 Payeer адрес: {payeer_address}"
        )
        bot.send_message(message.chat.id, "Запрос на вывод средств отправлен. Ожидайте обработки.")
        log_message(f"Запрос на вывод средств от пользователя {user_id}: {amount:.2f} рублей на адрес {payeer_address}.")
    else:
        bot.send_message(message.chat.id, "Введите корректный Payeer адрес.")
        bot.register_next_step_handler(message, process_payeer_address, amount)

@bot.message_handler(func=lambda message: message.text == "🆘 Тех. поддержка")
def support(message):
    bot.send_message(message.chat.id, f"Свяжитесь с тех. поддержкой: {SUPPORT_BOT_LINK}", reply_markup=back_to_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "🔧 Админка")
def admin_panel(message):
    if str(message.chat.id) == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📋 Ожидающие проверки токены")
        markup.add("📥 Скачать все токены")
        markup.add("🔙 Назад")
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Вы не являетесь администратором.")

@bot.message_handler(func=lambda message: message.text == "📋 Ожидающие проверки токены")
def review_pending_tokens(message):
    if str(message.chat.id) == ADMIN_ID:
        pending_tokens = {user_id: data['tokens'] for user_id, data in users_data.items() if data['tokens']}
        if pending_tokens:
            for user_id, tokens in pending_tokens.items():
                tokens_count = len(tokens)
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton(f"Одобрить ({tokens_count})", callback_data=f"approve_{user_id}_{tokens_count}"),
                    types.InlineKeyboardButton(f"Отклонить ({tokens_count})", callback_data=f"reject_{user_id}_{tokens_count}")
                )
                bot.send_message(message.chat.id, f"Токены пользователя {user_id}: {tokens_count} токенов.", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Нет токенов, ожидающих проверки.")
    else:
        bot.send_message(message.chat.id, "Вы не являетесь администратором.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_'))
def approve_tokens_callback(call):
    _, user_id, count = call.data.split('_')
    approve_tokens(user_id, int(count))
    bot.send_message(call.message.chat.id, f"Токены пользователя {user_id} одобрены.")
    log_message(f"Токены пользователя {user_id} одобрены (количество: {count}).")

@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_'))
def reject_tokens_callback(call):
    _, user_id, count = call.data.split('_')
    reject_tokens(user_id, int(count))
    bot.send_message(call.message.chat.id, f"Токены пользователя {user_id} отклонены.")
    log_message(f"Токены пользователя {user_id} отклонены (количество: {count}).")

@bot.message_handler(func=lambda message: message.text == "📥 Скачать все токены")
def download_all_tokens(message):
    if str(message.chat.id) == ADMIN_ID:
        with open('all_tokens.txt', 'w') as file:
            for token, user_id in tokens_data.items():
                file.write(f"{token} - {user_id}\n")
        with open('all_tokens.txt', 'rb') as file:
            bot.send_document(message.chat.id, file)
        log_message("Все токены были скачаны администратором.")
    else:
        bot.send_message(message.chat.id, "Вы не являетесь администратором.")

@bot.message_handler(func=lambda message: message.text == "🔙 Назад")
def back(message):
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=main_keyboard(str(message.chat.id)))

bot.polling(none_stop=True)
