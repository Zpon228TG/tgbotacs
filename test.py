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

# Клавиатуры
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

# Обработчики команд
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
    if message.text == "🔙 Назад":
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=back_to_main_keyboard())
        return
    
    payeer_address = message.text
    if payeer_address:
        # Отправка запроса в канал админа
        bot.send_message(
            CHANNEL_ID,
            f"💵 Запрос на вывод средств\n"
            f"🆔 ID пользователя: {message.chat.id}\n"
            f"💰 Сумма: {amount:.2f} рублей\n"
            f"📩 Адрес Payeer: {payeer_address}\n"
            f"✅ Нажмите 'Выплачено', чтобы подтвердить выплату.\n"
            f"🚫 Нажмите 'Отменить', чтобы отменить запрос.",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("✅ Выплачено", callback_data=f"confirm_withdrawal_{message.chat.id}_{amount}_{payeer_address}"),
                types.InlineKeyboardButton("🚫 Отменить", callback_data=f"cancel_withdrawal_{message.chat.id}")
            )
        )
        bot.send_message(message.chat.id, "Запрос на вывод отправлен на обработку.")
    else:
        bot.send_message(message.chat.id, "Введите корректный Payeer адрес.")
        bot.register_next_step_handler(message, process_payeer_address, amount)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_withdrawal"))
def confirm_withdrawal(call):
    try:
        _, user_id, amount, payeer_address = call.data.split("_", 3)
        user_id = str(user_id)
        amount = float(amount)

        if user_id in users_data:
            users_data[user_id]['balance'] = 0.0  # Обновление баланса пользователя

            # Отправка сообщения пользователю
            bot.send_message(user_id, "Выплата прошла успешно.")
            bot.send_message(user_id, "Выберите действие:", reply_markup=back_to_main_keyboard())

            # Отправка сообщения в канал админа
            bot.send_message(
                ADMIN_ID,
                f"Выплата {amount:.2f} рублей пользователю {user_id} на адрес {payeer_address} подтверждена."
            )
        else:
            bot.send_message(call.message.chat.id, "Пользователь не найден.")
    except ValueError:
        bot.send_message(call.message.chat.id, "Произошла ошибка при обработке выплаты.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_withdrawal"))
def cancel_withdrawal(call):
    try:
        _, user_id = call.data.split("_", 1)
        user_id = str(user_id)
        bot.send_message(user_id, "Запрос на вывод отменен.")
        bot.send_message(user_id, "Выберите действие:", reply_markup=back_to_main_keyboard())
    except ValueError:
        bot.send_message(call.message.chat.id, "Произошла ошибка при отмене запроса.")

@bot.message_handler(func=lambda message: message.text == "🔧 Админка" and str(message.chat.id) == ADMIN_ID)
def admin_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Проверить токены")
    markup.add("Скачать все токены")
    markup.add("🔙 Назад")
    bot.send_message(message.chat.id, "Админка", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Проверить токены" and str(message.chat.id) == ADMIN_ID)
def check_tokens(message):
    pending_users = [user_id for user_id, user_data in users_data.items() if user_data['tokens']]
    if pending_users:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for user_id in pending_users:
            markup.add(user_id)
        markup.add("🔙 Назад")
        bot.send_message(message.chat.id, "Выберите ID пользователя для проверки:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Нет токенов на проверке.")

@bot.message_handler(func=lambda message: str(message.chat.id) == ADMIN_ID and message.text in [user_id for user_id in users_data])
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
    bot.register_next_step_handler(message, process_token_approval, user_id)

def process_token_approval(message, user_id):
    if message.text == "Все токены подходят":
        approve_tokens(user_id, len(users_data[user_id]['tokens']))
        bot.send_message(message.chat.id, "Токены одобрены и добавлены на баланс пользователя.")
    elif message.text == "Не все подходят":
        bot.send_message(message.chat.id, "Введите количество подходящих токенов:")
        bot.register_next_step_handler(message, process_partial_approval, user_id)
    else:
        bot.send_message(message.chat.id, "Неверный выбор. Пожалуйста, попробуйте снова.")
        bot.send_message(message.chat.id, "Итог проверки:", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("Все токены подходят", "Не все подходят").add("🔙 Назад"))

def process_partial_approval(message, user_id):
    try:
        count = int(message.text)
        approve_tokens(user_id, count)
        bot.send_message(message.chat.id, f"{count} токенов одобрены и добавлены на баланс пользователя.")
    except ValueError:
        bot.send_message(message.chat.id, "Введите корректное число.")

@bot.message_handler(func=lambda message: message.text == "Скачать все токены" and str(message.chat.id) == ADMIN_ID)
def download_all_tokens(message):
    with open('all_tokens.txt', 'w') as file:
        for token in tokens_data:
            file.write(f"{token}\n")
    with open('all_tokens.txt', 'rb') as file:
        bot.send_document(message.chat.id, file)
    os.remove('all_tokens.txt')

bot.polling()
