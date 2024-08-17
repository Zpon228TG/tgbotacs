import telebot
import json
import os
from telebot import types

API_TOKEN = '7024190964:AAEzgPV9RvoJMbBBShBvSo-K5yEIsq08D4I'
CHANNEL_ID = '@GameDevAssetsHub'
LOG_CHANNEL_ID = '@YourLogChannelID'  # Замените на ваш канал для логирования
SUPPORT_BOT_LINK = 'https://t.me/your_support_bot'
TOKENS_FILE = 'tokens.json'
USERS_FILE = 'users.json'
ADMIN_ID = '6578018656'  # Замените на ваш ID

bot = telebot.TeleBot(API_TOKEN)

def load_json(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def log_action(message):
    bot.send_message(LOG_CHANNEL_ID, message)

def add_user(user_id):
    users_data = load_json(USERS_FILE)
    if str(user_id) not in users_data:
        users_data[str(user_id)] = {
            'balance': 0.0,
            'tokens_loaded': 0,
            'tokens_in_hold': 0.0
        }
        save_json(USERS_FILE, users_data)

def add_tokens(user_id, tokens):
    tokens_data = load_json(TOKENS_FILE)
    new_tokens = []
    for token in tokens:
        token = token.strip()
        if token and token not in tokens_data:
            tokens_data[token] = user_id
            new_tokens.append(token)
    if new_tokens:
        save_json(TOKENS_FILE, tokens_data)
        users_data = load_json(USERS_FILE)
        users_data[str(user_id)]['tokens_loaded'] += len(new_tokens)
        users_data[str(user_id)]['balance'] += len(new_tokens) * 0.01
        save_json(USERS_FILE, users_data)
        log_action(f"#TokenAdded - Пользователь {user_id} добавил {len(new_tokens)} токенов")
        return len(new_tokens)
    return 0

def main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ['Загрузить токены', 'Профиль', 'Вывести деньги', 'Тех. поддержка']
    keyboard.add(*buttons)
    return keyboard

def back_to_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ['Загрузить токены', 'Профиль', 'Вывести деньги', 'Тех. поддержка']
    keyboard.add(*buttons)
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    add_user(user_id)
    bot.send_message(message.chat.id, "Привет! Выберите действие:", reply_markup=main_keyboard())
    log_action(f"#NewUser - {user_id} запустил бота")

@bot.message_handler(func=lambda message: message.text == 'Загрузить токены')
def upload_tokens(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Через файл", "Через бота", "🔙 Назад")
    bot.send_message(message.chat.id, "Как вы хотите загрузить токены?", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Через файл")
def upload_tokens_file(message):
    bot.send_message(message.chat.id, "Отправьте файл с токенами.")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == 'text/plain':
        user_id = message.from_user.id
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
            count = add_tokens(message.from_user.id, tokens)
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

@bot.message_handler(func=lambda message: message.text == 'Профиль')
def profile(message):
    user_id = message.from_user.id
    users_data = load_json(USERS_FILE)
    user_info = users_data.get(str(user_id), None)
    if user_info:
        profile_text = (f"🆔 Ваш ID: {user_id}\n"
                        f"💰 Баланс: {user_info['balance']:.2f} руб.\n"
                        f"🔢 Количество загруженных токенов: {user_info['tokens_loaded']}\n"
                        f"💼 Сумма в холде: {user_info['tokens_in_hold']:.2f} руб.")
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton('Вывести деньги'))
        bot.send_message(message.chat.id, profile_text, reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "Пользователь не найден.")

@bot.message_handler(func=lambda message: message.text == 'Вывести деньги')
def request_withdrawal(message):
    msg = bot.send_message(message.chat.id, "Введите сумму для вывода (минимум 5 рублей).")
    bot.register_next_step_handler(msg, process_withdrawal_request)

def process_withdrawal_request(message):
    user_id = message.from_user.id
    amount = float(message.text)
    if amount < 5:
        bot.send_message(message.chat.id, "Минимальная сумма для вывода - 5 рублей.")
        return

    users_data = load_json(USERS_FILE)
    user_info = users_data.get(str(user_id), None)
    if user_info and user_info['balance'] >= amount:
        user_info['tokens_in_hold'] += amount
        user_info['balance'] -= amount
        save_json(USERS_FILE, users_data)

        request_text = (f"💵 Запрос на вывод средств\n"
                        f"🆔 ID пользователя: {user_id}\n"
                        f"💰 Сумма: {amount:.2f} рублей\n"
                        f"📩 Адрес Payeer: {message.text}\n"
                        f"✅ Нажмите 'Выплачено', чтобы подтвердить выплату.\n"
                        f"🚫 Нажмите 'Отменить', чтобы отменить запрос.")
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("Выплачено", callback_data=f'confirm_{user_id}_{amount}'),
            types.InlineKeyboardButton("Отменить", callback_data=f'cancel_{user_id}')
        )
        bot.send_message(CHANNEL_ID, request_text, reply_markup=keyboard)
        bot.send_message(message.chat.id, "Ваш запрос на вывод средств отправлен на обработку.")
        log_action(f"#WithdrawRequest - Пользователь {user_id} запросил вывод {amount:.2f} рублей")
    else:
        bot.send_message(message.chat.id, "Недостаточно средств на балансе.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_'))
def confirm_withdrawal(call):
    _, user_id, amount = call.data.split('_')
    user_id = int(user_id)
    amount = float(amount)

    users_data = load_json(USERS_FILE)
    user_info = users_data.get(str(user_id), None)
    if user_info:
        user_info['tokens_in_hold'] -= amount
        save_json(USERS_FILE, users_data)
        bot.send_message(CHANNEL_ID, f"💵 Выплачено: {amount:.2f} рублей пользователю {user_id}")
        bot.send_message(call.message.chat.id, "Выплата прошла успешно.")
        log_action(f"#WithdrawalSuccess - Выплачено {amount:.2f} рублей пользователю {user_id}")
    else:
        bot.send_message(call.message.chat.id, "Пользователь не найден.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_'))
def cancel_withdrawal(call):
    user_id = call.data.split('_')[1]
    bot.send_message(call.message.chat.id, "Ваш запрос на вывод средств отменен.")
    log_action(f"#WithdrawalCancelled - Запрос на вывод средств пользователем {user_id} отменен")

@bot.message_handler(func=lambda message: message.text == 'Тех. поддержка')
def tech_support(message):
    bot.send_message(message.chat.id, f"Для получения технической поддержки напишите в наш бот: {SUPPORT_BOT_LINK}")

if __name__ == "__main__":
    bot.polling(none_stop=True)
