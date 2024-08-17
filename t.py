import telebot
from telebot import types
import json
import os

API_TOKEN = '7024190964:AAEzgPV9RvoJMbBBShBvSo-K5yEIsq08D4I'
CHANNEL_ID = '@GameDevAssetsHub'
LOG_CHANNEL_ID = '@GameDevAssetsHub'  # Замените на ваш канал для логирования
SUPPORT_BOT_LINK = 'https://t.me/your_support_bot'
TOKENS_FILE = 'tokens.json'
USERS_FILE = 'users.json'
ADMIN_ID = '6578018656'  # Ваш ID

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

def log_action(message):
    bot.send_message(LOG_CHANNEL_ID, message)

tokens_data = load_data(TOKENS_FILE)
users_data = load_data(USERS_FILE)

def add_user(user_id):
    user_id_str = str(user_id)
    if user_id_str not in users_data:
        users_data[user_id_str] = {
            'balance': 0.0,
            'tokens': [],
            'hold': 0.0,
            'total_tokens': 0
        }
        save_data(USERS_FILE, users_data)
        log_action(f"#NewUser - {user_id_str} запустил бота")

def add_tokens(user_id, tokens):
    user_id_str = str(user_id)
    tokens_data = load_data(TOKENS_FILE)
    unique_tokens = [token for token in tokens if token not in tokens_data]
    if unique_tokens:
        users_data[user_id_str]['tokens'].extend(unique_tokens)
        users_data[user_id_str]['hold'] += 0.01 * len(unique_tokens)
        users_data[user_id_str]['total_tokens'] += len(unique_tokens)
        tokens_data.update({token: user_id_str for token in unique_tokens})
        save_data(USERS_FILE, users_data)
        save_data(TOKENS_FILE, tokens_data)
        log_action(f"#TokenAdded - Пользователь {user_id_str} добавил {len(unique_tokens)} токенов")
    return len(unique_tokens)

def approve_tokens(user_id, count):
    user_id_str = str(user_id)
    if user_id_str in users_data:
        users_data[user_id_str]['balance'] += 0.01 * count
        users_data[user_id_str]['hold'] -= 0.01 * count
        users_data[user_id_str]['tokens'] = []
        save_data(USERS_FILE, users_data)
        log_action(f"#TokensApproved - {user_id_str} одобрил {count} токенов")

def reject_tokens(user_id, count):
    user_id_str = str(user_id)
    if user_id_str in users_data:
        users_data[user_id_str]['hold'] -= 0.01 * count
        users_data[user_id_str]['tokens'] = []
        save_data(USERS_FILE, users_data)
        log_action(f"#TokensRejected - {user_id_str} отклонил {count} токенов")

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
    user_id = message.chat.id
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
        user_id = message.chat.id
        file_info = bot.get_file(message.document.file_id)
        file = bot.download_file(file_info.file_path)
        tokens = file.decode('utf-8').splitlines()
        count = add_tokens(user_id, tokens)
        if count > 0:
            bot.send_message(message.chat.id, f"Токены загружены. На проверке: {count} токенов. 💰 Ваш баланс будет обновлен после проверки.")
        else:
            bot.send_message(message.chat.id, "Все токены уже существуют.")
        log_action(f"#TokensUploaded - Пользователь {user_id} загрузил файл с токенами")
    else:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте текстовый файл (.txt).")

@bot.message_handler(func=lambda message: message.text == "Через бота")
def upload_tokens_via_bot(message):
    bot.send_message(message.chat.id, "Введите токены по одному (максимум 15). Когда закончите, введите 'Готово'.")
    bot.register_next_step_handler(message, collect_tokens, [])

def collect_tokens(message, tokens):
    if message.text.lower() == 'готово' or len(tokens) == 15:
        if tokens:
            count = add_tokens(message.chat.id, tokens)
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
    user_id = message.chat.id
    user_data = users_data.get(str(user_id), {})
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
    user_id = call.message.chat.id
    balance = users_data.get(str(user_id), {}).get('balance', 0.0)
    if balance >= 5:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🔙 Назад")
        bot.send_message(call.message.chat.id, "Введите сумму для вывода (минимум 5 рублей):", reply_markup=markup)
        bot.register_next_step_handler(call.message, process_withdrawal_amount)
    else:
        bot.send_message(call.message.chat.id, "Сумма для вывода должна быть не меньше 5 рублей.")

def process_withdrawal_amount(message):
    user_id = message.chat.id
    try:
        amount = float(message.text)
        if amount >= 5 and amount <= users_data.get(str(user_id), {}).get('balance', 0.0):
            bot.send_message(ADMIN_ID, f"Пользователь {user_id} запросил вывод {amount:.2f} рублей.")
            bot.send_message(message.chat.id, "Запрос на вывод средств отправлен администратору.")
            log_action(f"#WithdrawalRequested - Пользователь {user_id} запросил вывод {amount:.2f} рублей")
        else:
            bot.send_message(message.chat.id, "Введите корректную сумму для вывода.")
            bot.register_next_step_handler(message, process_withdrawal_amount)
    except ValueError:
        bot.send_message(message.chat.id, "Введите корректную сумму.")

@bot.message_handler(func=lambda message: message.text == "🆘 Тех. поддержка")
def tech_support(message):
    bot.send_message(message.chat.id, f"Для получения технической поддержки, перейдите по [ссылке]({SUPPORT_BOT_LINK})", parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "🔧 Админка")
def admin_panel(message):
    if str(message.chat.id) == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🔄 Проверка токенов")
        markup.add("📜 Скачать все токены")
        markup.add("🔙 Назад")
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к админке.")

@bot.message_handler(func=lambda message: message.text == "🔄 Проверка токенов")
def check_tokens(message):
    if str(message.chat.id) == ADMIN_ID:
        for user_id_str, user_data in users_data.items():
            tokens = user_data['tokens']
            if tokens:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("✅ Все токены подходят", callback_data=f"approve_{user_id_str}"))
                markup.add(types.InlineKeyboardButton("❌ Не все подходят", callback_data=f"reject_{user_id_str}"))
                bot.send_message(message.chat.id, f"Пользователь {user_id_str} ждет проверки токенов.", reply_markup=markup)
            else:
                bot.send_message(message.chat.id, f"У пользователя {user_id_str} нет токенов на проверке.")
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к админке.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def approve_tokens_callback(call):
    user_id_str = call.data.split("_")[1]
    approve_tokens(user_id_str, len(users_data[user_id_str]['tokens']))
    bot.answer_callback_query(call.id, "Токены одобрены.")
    bot.send_message(call.message.chat.id, f"Токены пользователя {user_id_str} одобрены.")
    log_action(f"#TokensApprovedByAdmin - {user_id_str} одобрен")

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject_tokens_callback(call):
    user_id_str = call.data.split("_")[1]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔙 Назад")
    bot.send_message(call.message.chat.id, "Введите количество подходящих токенов для учета на баланс пользователя:", reply_markup=markup)
    bot.register_next_step_handler(call.message, process_rejection_amount, user_id_str)

def process_rejection_amount(message, user_id_str):
    try:
        count = int(message.text)
        if count >= 0:
            reject_tokens(user_id_str, count)
            bot.send_message(message.chat.id, f"Токены пользователя {user_id_str} отклонены. {count} токенов учтено.")
            log_action(f"#TokensRejectedByAdmin - {user_id_str} отклонен. Учтено {count} токенов")
        else:
            bot.send_message(message.chat.id, "Введите корректное количество токенов.")
            bot.register_next_step_handler(message, process_rejection_amount, user_id_str)
    except ValueError:
        bot.send_message(message.chat.id, "Введите корректное количество токенов.")
        bot.register_next_step_handler(message, process_rejection_amount, user_id_str)

@bot.message_handler(func=lambda message: message.text == "📜 Скачать все токены")
def download_all_tokens(message):
    if str(message.chat.id) == ADMIN_ID:
        if tokens_data:
            with open('all_tokens.txt', 'w') as file:
                for token, user_id in tokens_data.items():
                    file.write(f"{token}\n")
            with open('all_tokens.txt', 'rb') as file:
                bot.send_document(message.chat.id, file, caption="Все токены")
            log_action("#TokensFileDownloaded - Все токены скачаны администратором")
        else:
            bot.send_message(message.chat.id, "Нет токенов для скачивания.")
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к админке.")

@bot.message_handler(func=lambda message: message.text == "🔙 Назад")
def back(message):
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=main_keyboard(message.chat.id))

bot.polling()
