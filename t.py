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
    users_data[user_id]['hold'] -= 0.01 * count
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

            users_data[user_id]['balance'] -= amount
            users_data[user_id]['hold'] -= amount
            save_data(USERS_FILE, users_data)

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("🔙 Назад"))
            bot.send_message(message.chat.id, f"Введите Payeer адрес для вывода {net_amount:.2f} рублей (с учетом комиссии {fee:.2f} рублей):", reply_markup=markup)
            bot.register_next_step_handler(message, process_payeer_address, net_amount)
        else:
            bot.send_message(message.chat.id, "Введите корректную сумму (минимум 5 рублей и не больше вашего баланса).")
            bot.register_next_step_handler(message, process_withdrawal_amount)
    except ValueError:
        bot.send_message(message.chat.id, "Введите корректное число.")
        bot.register_next_step_handler(message, process_withdrawal_amount)

def process_payeer_address(message, amount):
    user_id = str(message.chat.id)
    payeer_address = message.text.strip()
    if re.match(r'^\d+$', payeer_address):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Выплачено", callback_data=f"paid_{user_id}_{amount}"))
        markup.add(types.InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{user_id}_{amount}"))
        bot.send_message(
            CHANNEL_ID,
            f"💵 Запрос на вывод средств\n"
            f"🆔 ID пользователя: {user_id}\n"
            f"💰 Сумма: {amount:.2f} рублей\n"
            f"📩 Адрес Payeer: {payeer_address}\n",
            reply_markup=markup
        )
        log_message(f"Запрос на вывод средств: ID пользователя {user_id}, Сумма {amount:.2f}, Адрес Payeer {payeer_address}.")
        bot.send_message(message.chat.id, "Запрос на вывод отправлен. Ожидайте подтверждения.")
    else:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный адрес Payeer (только цифры).")
        bot.register_next_step_handler(message, process_payeer_address, amount)

@bot.callback_query_handler(func=lambda call: call.data.startswith("paid_"))
def paid_callback(call):
    _, user_id, amount = call.data.split("_")
    amount = float(amount)
    bot.send_message(call.message.chat.id, f"✅ Успешно выплатили {amount:.2f} рублей на указанный адрес.")
    bot.send_message(user_id, f"✅ Успешно выплатили {amount:.2f} рублей на указанный адрес.")
    log_message(f"Выплата {amount:.2f} рублей успешно выполнена для пользователя {user_id}.")
    bot.edit_message_text("Запрос на вывод средств был успешно выполнен.", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_"))
def cancel_callback(call):
    _, user_id, amount = call.data.split("_")
    amount = float(amount)
    bot.send_message(call.message.chat.id, "❌ Запрос на вывод средств отменен.")
    bot.send_message(user_id, "❌ Запрос на вывод средств отменен.")
    log_message(f"Запрос на вывод средств в размере {amount:.2f} рублей был отменен для пользователя {user_id}.")
    bot.edit_message_text("Запрос на вывод средств был отменен.", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda message: message.text == "🆘 Тех. поддержка")
def support(message):
    bot.send_message(message.chat.id, f"Если у вас возникли вопросы, обратитесь в тех. поддержку: {SUPPORT_BOT_LINK}")

@bot.message_handler(func=lambda message: message.text == "🔧 Админка")
def admin_panel(message):
    if str(message.chat.id) == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📋 Проверить токены")
        markup.add("📄 Скачать все токены")
        markup.add("🔙 Назад")
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Вы не авторизованы для доступа к админке.")

@bot.message_handler(func=lambda message: message.text == "📋 Проверить токены")
def check_tokens(message):
    if str(message.chat.id) == ADMIN_ID:
        markup = types.InlineKeyboardMarkup()
        for user_id in users_data:
            markup.add(types.InlineKeyboardButton(f"Пользователь {user_id}", callback_data=f"check_{user_id}"))
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_admin"))
        bot.send_message(message.chat.id, "Выберите пользователя для проверки токенов:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Вы не авторизованы для доступа к админке.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("check_"))
def check_user_tokens(call):
    user_id = call.data.split("_")[1]
    tokens = users_data.get(user_id, {}).get('tokens', [])
    if tokens:
        tokens_list = '\n'.join(tokens)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Все токены подходят", callback_data=f"approve_{user_id}_{len(tokens)}"))
        markup.add(types.InlineKeyboardButton("❌ Не все токены подходят", callback_data=f"reject_{user_id}_{len(tokens)}"))
        bot.send_message(
            call.message.chat.id,
            f"Токены пользователя {user_id}:\n{tokens_list}",
            reply_markup=markup
        )
    else:
        bot.send_message(call.message.chat.id, f"У пользователя {user_id} нет токенов на проверке.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def approve_tokens_callback(call):
    user_id, count = call.data.split("_")[1], int(call.data.split("_")[2])
    approve_tokens(user_id, count)
    bot.send_message(call.message.chat.id, f"Токены пользователя {user_id} одобрены. {count} токенов учтены на балансе.")
    log_message(f"Администратор одобрил {count} токенов пользователя {user_id}.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject_tokens_callback(call):
    user_id, count = call.data.split("_")[1], int(call.data.split("_")[2])
    reject_tokens(user_id, count)
    bot.send_message(call.message.chat.id, f"Токены пользователя {user_id} отклонены. {count} токенов не учтены.")
    log_message(f"Администратор отклонил {count} токенов пользователя {user_id}.")

@bot.callback_query_handler(func=lambda call: call.data == "back_to_admin")
def back_to_admin(call):
    bot.edit_message_text("Выберите действие:", call.message.chat.id, call.message.message_id, reply_markup=admin_panel_keyboard())

@bot.message_handler(func=lambda message: message.text == "📄 Скачать все токены")
def download_all_tokens(message):
    if str(message.chat.id) == ADMIN_ID:
        tokens_list = '\n'.join(tokens_data.keys())
        with open('all_tokens.txt', 'w') as file:
            file.write(tokens_list)
        with open('all_tokens.txt', 'rb') as file:
            bot.send_document(message.chat.id, file, caption="Список всех токенов.")
    else:
        bot.send_message(message.chat.id, "Вы не авторизованы для доступа к админке.")

def admin_panel_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📋 Проверить токены", callback_data="check_tokens"))
    markup.add(types.InlineKeyboardButton("📄 Скачать все токены", callback_data="download_all_tokens"))
    return markup

bot.polling()
