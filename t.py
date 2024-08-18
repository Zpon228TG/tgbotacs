import time
import requests
import telebot
from telebot import types
import json
import os
import threading
import re
import random
import string


# Укажите ваш токен здесь
API_TOKEN = '7024190964:AAEzgPV9RvoJMbBBShBvSo-K5yEIsq08D4I'
CHANNEL_ID = '@GameDevAssetsHub'
LOG_CHANNEL_ID_TOKENS = '@GameDevAssetsHub'  # Новый канал для логирования проверки токенов
SUPPORT_BOT_LINK = 'https://t.me/your_support_bot'
TOKENS_FILE = 'tokens.json'
USERS_FILE = 'users.json'
ADMIN_ID = '6578018656'  # Ваш ID
BLOCKED_USERS_FILE = 'blocked_users.json'

# Процент комиссии на вывод
WITHDRAWAL_FEE_PERCENT = 1.5

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
            'total_tokens': 0,
            'accepted_rules': False  # Добавлено для проверки согласия с правилами
        }
        save_data(USERS_FILE, users_data)


def generate_tokens_filename(user_id):
    return f"{user_id}_working_tokens.txt"

# Загрузим данные заблокированных пользователей
blocked_users_data = load_data(BLOCKED_USERS_FILE) or {}

def save_blocked_users():
    save_data(BLOCKED_USERS_FILE, blocked_users_data)

def add_tokens(user_id, tokens):
    global tokens_data
    if not isinstance(tokens_data, dict):
        tokens_data = {}

    unique_tokens = [token for token in tokens if token not in tokens_data]
    working_tokens = []
    non_working_tokens = []

    if unique_tokens:
        if can_send_message(user_id):
            checking_message = bot.send_message(user_id, "Проверяю токены, ожидайте...")

        def check_tokens():
            nonlocal working_tokens, non_working_tokens

            def worker(token):
                if check_token(token):
                    working_tokens.append(token)
                else:
                    non_working_tokens.append(token)
                time.sleep(0.5)

            threads = []
            for token in unique_tokens:
                thread = threading.Thread(target=worker, args=(token,))
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()

            for token in working_tokens:
                tokens_data[token] = user_id
                users_data[user_id]['tokens'].append(token)

            # Обновление баланса
            total_working = len(working_tokens)
            total_amount = total_working * 0.01
            users_data[user_id]['balance'] += total_amount  # Добавление средств к балансу
            users_data[user_id]['total_tokens'] += len(tokens)  # Обновление количества загруженных токенов

            save_data(USERS_FILE, users_data)
            save_data(TOKENS_FILE, tokens_data)

            total_non_working = len(non_working_tokens)

            # Отправляем информацию пользователю после проверки токенов
            if can_send_message(user_id):
                bot.send_message(
                    user_id,
                    f"Рабочих: {total_working}\nНерабочих: {total_non_working}\nВам зачислено: {total_amount:.2f} рублей"
                )
                bot.send_message(user_id, f"🪙 Всего токенов загружено: {len(tokens)}")

            # Генерация и отправка файла с рабочими токенами
            if total_working > 0:
                filename = generate_tokens_filename(user_id)
                with open(filename, 'w', encoding='utf-8') as file:
                    for token in working_tokens:
                        file.write(token + '\n')

                log_message(f"#Токены{user_id} Файл с рабочими токенами успешно создан.")
                try:
                    with open(filename, 'rb') as file:
                        bot.send_document(LOG_CHANNEL_ID_TOKENS, file, caption="Файл с рабочими токенами успешно создан.")
                except FileNotFoundError:
                    log_message(f"#Токены{user_id} Ошибка при отправке файла. Файл не найден.")
                except UnicodeEncodeError:
                    log_message(f"#Токены{user_id} Ошибка кодировки при отправке файла.")
                finally:
                    if os.path.exists(filename):
                        os.remove(filename)  # Удаление файла после отправки
            else:
                log_message(f"#Checktoken{user_id} Всего токенов: Рабочих: 0, Не рабочих: {total_non_working}")

            if can_send_message(user_id):
                bot.delete_message(user_id, checking_message.message_id)

        threading.Thread(target=check_tokens).start()
        return len(unique_tokens)
    else:
        if can_send_message(user_id):
            bot.send_message(user_id, "Все токены уже существуют.")
        return 0




def check_token(token):
    url = "https://id.twitch.tv/oauth2/validate"
    headers = {"Authorization": f"OAuth {token}".encode('utf-8')}
    response = requests.get(url, headers=headers)
    return response.status_code == 200

# Функция для перезапуска бота
def restart_bot():
    subprocess.Popen(['python', 'bot.py'])

def log_message(message):
    try:
        bot.send_message(LOG_CHANNEL_ID_TOKENS, message)
    except telebot.apihelper.ApiTelegramException as e:
        error_code = e.result_json.get('error_code', None)
        if error_code == 400:
            log_message(f"Ошибка при отправке сообщения: неверный запрос. Код ошибки: {error_code}")
        elif error_code == 429:
            time.sleep(30)
            log_message(message)
        else:
            log_message(f"Неизвестная ошибка при отправке сообщения. Код ошибки: {error_code}")
    except UnicodeEncodeError:
        # Логируем ошибку кодировки
        bot.send_message(LOG_CHANNEL_ID_TOKENS, "Ошибка кодировки при отправке сообщения.")






def download_tokens():
    filename = 'working_tokens.txt'
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        for token in tokens_data.keys():
            file.write(token + '\n')

    # Проверка, что файл не пустой перед отправкой
    if os.path.getsize(filename) == 0:
        log_message("Ошибка: файл с токенами пуст.")



last_message_times = {}

def can_send_message(user_id):
    current_time = time.time()
    last_time = last_message_times.get(user_id, 0)
    if current_time - last_time >= 5:
        last_message_times[user_id] = current_time
        return True
    return False



def main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📥 Загрузить токены"))
    markup.add(types.KeyboardButton("💼 Профиль"))
    markup.add(types.KeyboardButton("🆘 Тех. поддержка"))
    if user_id == ADMIN_ID:
        markup.add(types.KeyboardButton("🔧 Админка"))
    return markup

def back_to_main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📥 Загрузить токены"))
    markup.add(types.KeyboardButton("💼 Профиль"))
    markup.add(types.KeyboardButton("🆘 Тех. поддержка"))
    if user_id == ADMIN_ID:
        markup.add(types.KeyboardButton("🔧 Админка"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    add_user(user_id)
    if user_id not in blocked_users_data:
        log_message(f"#НовыйПользователь{user_id} Новый пользователь начал использовать бота.")
    if not users_data[user_id]['accepted_rules']:
        bot.send_message(user_id, "Привет! Добро пожаловать! Пожалуйста, ознакомьтесь с правилами использования бота - (https://your_rules_link). Для продолжения нажмите 'Согласен с правилами использования'.")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Согласен с правилами использования"))
        bot.send_message(user_id, "Вы должны согласиться с правилами использования, чтобы продолжить.", reply_markup=markup)
    else:
        bot.send_message(user_id, "Привет! Выберите действие:", reply_markup=main_keyboard(user_id))



@bot.message_handler(func=lambda message: message.text == "Согласен с правилами использования")
def accept_rules(message):
    user_id = str(message.chat.id)
    users_data[user_id]['accepted_rules'] = True
    save_data(USERS_FILE, users_data)
    bot.send_message(user_id, "Спасибо за согласие с правилами! Теперь вы можете использовать все функции бота.", reply_markup=main_keyboard(user_id))



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
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=back_to_main_keyboard(user_id))
    else:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте текстовый файл (.txt).")

@bot.message_handler(func=lambda message: message.text == "Через бота")
def upload_tokens_via_bot(message):
    user_id = str(message.chat.id)  # Получаем user_id
    bot.send_message(message.chat.id, "Введите токены по одному (максимум 15). Когда закончите, введите 'Готово'.")
    bot.register_next_step_handler(message, collect_tokens, [], user_id)  # Передаем user_id


def collect_tokens(message, tokens, user_id):
    if message.text.lower() == 'готово' or len(tokens) == 15:
        if tokens:
            count = add_tokens(user_id, tokens)
            if count > 0:
                bot.send_message(message.chat.id, f"Токены загружены. На проверке: {count} токенов. 💰 Ваш баланс будет обновлен после проверки.")
            else:
                bot.send_message(message.chat.id, "Все токены уже существуют.")
        else:
            bot.send_message(message.chat.id, "Вы не ввели ни одного токена.")
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=back_to_main_keyboard(user_id))
    else:
        tokens.append(message.text)
        bot.send_message(message.chat.id, f"Токен {len(tokens)}/15 добавлен.")
        bot.register_next_step_handler(message, collect_tokens, tokens, user_id)


@bot.message_handler(func=lambda message: message.text == "💼 Профиль")
def profile(message):
    user_id = str(message.chat.id)
    user_data = users_data.get(user_id, {})
    balance = user_data.get('balance', 0.0)
    total_tokens = user_data.get('total_tokens', 0)

    profile_text = (
        f"🆔 Ваш ID: {user_id}\n"
        f"💰 Баланс: {balance:.2f} рублей\n"
        f"🪙 Всего токенов загружено: {total_tokens}"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💸 Вывести деньги", callback_data="withdraw"))
    markup.add(types.InlineKeyboardButton("📝 Отзывы", url="https://t.me/your_feedback_channel"))
    markup.add(types.InlineKeyboardButton("Правила использования бота", url="https://playerok.com/profile/ArseniyX/products"))
    bot.send_message(message.chat.id, profile_text, reply_markup=markup)



@bot.callback_query_handler(func=lambda call: call.data.startswith("withdraw"))
def process_withdrawal_amount(call):
    user_id = str(call.message.chat.id)  # Исправлено здесь
    try:
        amount = float(call.message.text)  # Исправлено здесь
        if amount < 5:
            bot.send_message(call.message.chat.id, "Вам не хватает баланса. Загрузите как можно больше рабочих токенов.")
            bot.register_next_step_handler(call.message, process_withdrawal_amount)
        elif amount <= users_data.get(user_id, {}).get('balance', 0.0):
            # Рассчитываем комиссию
            fee = amount * (WITHDRAWAL_FEE_PERCENT / 100)
            net_amount = amount - fee

            # Убираем средства с баланса и не затрагиваем холд
            users_data[user_id]['balance'] -= net_amount
            save_data(USERS_FILE, users_data)

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("🔙 Назад"))
            bot.send_message(call.message.chat.id, f"Введите Payeer адрес для вывода {net_amount:.2f} рублей (с учетом комиссии {fee:.2f} рублей):", reply_markup=markup)
            bot.register_next_step_handler(call.message, process_payeer_address, net_amount, fee)
        else:
            bot.send_message(call.message.chat.id, "Введите корректную сумму (минимум 5 рублей и не больше вашего баланса).")
            bot.register_next_step_handler(call.message, process_withdrawal_amount)
    except ValueError:
        bot.send_message(call.message.chat.id, "Введите корректную сумму.")
        bot.register_next_step_handler(call.message, process_withdrawal_amount)




@bot.message_handler(func=lambda message: message.text == "🔙 Назад")
def go_back(message):
    user_id = str(message.chat.id)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=back_to_main_keyboard(user_id))



def process_withdrawal_amount(message):
    user_id = str(message.chat.id)
    try:
        amount = float(message.text)
        if amount >= 5 and amount <= users_data.get(user_id, {}).get('balance', 0.0):
            # Рассчитываем комиссию
            fee = amount * (WITHDRAWAL_FEE_PERCENT / 100)
            net_amount = amount - fee

            # Убираем средства с баланса и не затрагиваем холд
            users_data[user_id]['balance'] -= net_amount  # Исправлено здесь
            save_data(USERS_FILE, users_data)
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("🔙 Назад"))
            bot.send_message(message.chat.id, f"Введите Payeer адрес для вывода {net_amount:.2f} рублей (с учетом комиссии {fee:.2f} рублей):", reply_markup=markup)
            bot.register_next_step_handler(message, process_payeer_address, net_amount, fee)
        else:
            bot.send_message(message.chat.id, "Введите корректную сумму (минимум 5 рублей и не больше вашего баланса).")
            bot.register_next_step_handler(message, process_withdrawal_amount)
    except ValueError:
        bot.send_message(message.chat.id, "Введите корректную сумму.")
        bot.register_next_step_handler(message, process_withdrawal_amount)


def process_payeer_address(message, net_amount, fee):
    user_id = str(message.chat.id)
    payeer_address = message.text.strip()
    
    if re.match(r'^\d+$', payeer_address):  # Разрешаем только цифры
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Верно", callback_data=f"confirm_{user_id}_{net_amount}_{fee}"))
        markup.add(types.InlineKeyboardButton("❌ Исправить", callback_data=f"edit_{user_id}_{net_amount}_{fee}"))
        bot.send_message(
            message.chat.id,
            f"Проверьте корректность введенного Payeer кошелька: {payeer_address}\nВерно ли указанный адрес?",
            reply_markup=markup
        )
    else:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный адрес Payeer (только цифры).")
        bot.register_next_step_handler(message, process_payeer_address, net_amount, fee)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def confirm_payeer_address(call):
    _, user_id, net_amount, fee = call.data.split("_")
    net_amount, fee = float(net_amount), float(fee)
    
    # Оформляем вывод средств
    bot.send_message(
        CHANNEL_ID,
        f"💵 Запрос на вывод средств\n"
        f"🆔 ID пользователя: {user_id}\n"
        f"💰 Сумма: {net_amount:.2f} рублей\n"
        f"📩 Адрес Payeer: {call.message.text}\n",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("✅ Выплачено", callback_data=f"paid_{user_id}_{net_amount}"),
            types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user_id}_{net_amount}_{fee}")
        )
    )
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "Запрос на вывод отправлен. Ожидайте подтверждения.")
    log_message(f"#Вывод{user_id} Сумма {net_amount:.2f}, Адрес Payeer {call.message.text}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
def edit_payeer_address(call):
    _, user_id, net_amount, fee = call.data.split("_")
    bot.send_message(
        call.message.chat.id,
        "Введите правильный адрес Payeer:",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
            types.KeyboardButton("🔙 Назад")
        )
    )
    bot.register_next_step_handler(call.message, process_payeer_address, float(net_amount), float(fee))
    bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("paid_"))
def paid_callback(call):
    _, user_id, net_amount = call.data.split("_")
    net_amount = float(net_amount)
    bot.send_message(call.message.chat.id, f"✅ Успешно выплатили {net_amount:.2f} рублей на указанный адрес. Спасибо что вы с нами!")
    bot.send_message(user_id, f"✅ Успешно выплатили {net_amount:.2f} рублей на указанный адрес. Спасибо что вы с нами!")
    log_message(f"#Выплата{user_id} Выплата {net_amount:.2f} рублей успешно выполнена.")
    bot.edit_message_text("Запрос на вывод средств был успешно выполнен.", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_"))
def cancel_callback(call):
    _, user_id, amount, fee = call.data.split("_")
    amount, fee = float(amount), float(fee)
    users_data[user_id]['balance'] += amount  # Возвращаем деньги на баланс
    users_data[user_id]['balance'] -= fee  # Уменьшаем холд на сумму комиссии
    save_data(USERS_FILE, users_data)
    
    bot.send_message(call.message.chat.id, "❌ Запрос на вывод средств отменен. Обратитесь в тех. поддержку для объяснений!")
    bot.send_message(user_id, "❌ Запрос на вывод средств отменен. Обратитесь в тех. поддержку для объяснений!")
    log_message(f"#Отменавыплата{user_id} Запрос на вывод средств в размере {amount:.2f} рублей был отменен.")
    bot.edit_message_text("Запрос на вывод средств был отменен.", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda message: message.text == "🔧 Админка")
def admin_panel(message):
    if str(message.chat.id) == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("📥 Скачать токены"))
        markup.add(types.KeyboardButton("🗨 Рассылка"))
        markup.add(types.KeyboardButton("🔍 Управление пользователями"))
        markup.add(types.KeyboardButton("🔙 Назад"))
        bot.send_message(message.chat.id, "Админка", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "🔍 Управление пользователями")
def user_management(message):
    if str(message.chat.id) == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("🔎 Поиск по ID"))
        markup.add(types.KeyboardButton("🚫 Блокировка пользователя"))
        markup.add(types.KeyboardButton("🔓 Разблокировка пользователя"))
        markup.add(types.KeyboardButton("📋 Список разблокированных пользователей"))
        markup.add(types.KeyboardButton("🔙 Назад"))
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "🔎 Поиск по ID")
def search_user_by_id(message):
    if str(message.chat.id) == ADMIN_ID:
        bot.send_message(message.chat.id, "Введите ID пользователя для поиска:")
        bot.register_next_step_handler(message, search_user_by_id_process)


def search_user_by_id_process(message):
    user_id = message.text.strip()
    if user_id in users_data:
        user_info = users_data[user_id]
        bot.send_message(
            message.chat.id,
            f"🆔 ID: {user_id}\n💰 Баланс: {user_info['balance']:.2f}\n🪙 Всего токенов: {user_info['total_tokens']}"
        )
    else:
        bot.send_message(message.chat.id, "Пользователь не найден.")
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=user_management(message))


@bot.message_handler(func=lambda message: message.text == "🚫 Блокировка пользователя")
def block_user(message):
    if str(message.chat.id) == ADMIN_ID:
        bot.send_message(message.chat.id, "Введите ID пользователя для блокировки:")
        bot.register_next_step_handler(message, block_user_process)


def block_user_process(message):
    user_id = message.text.strip()
    if user_id in users_data:
        blocked_users_data[user_id] = users_data[user_id]
        save_blocked_users()
        del users_data[user_id]
        save_data(USERS_FILE, users_data)
        bot.send_message(message.chat.id, f"Пользователь {user_id} заблокирован.")
    else:
        bot.send_message(message.chat.id, "Пользователь не найден.")
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=user_management(message))


@bot.message_handler(func=lambda message: message.text == "🔓 Разблокировка пользователя")
def unblock_user(message):
    if str(message.chat.id) == ADMIN_ID:
        bot.send_message(message.chat.id, "Введите ID пользователя для разблокировки:")
        bot.register_next_step_handler(message, unblock_user_process)


def unblock_user_process(message):
    user_id = message.text.strip()
    if user_id in blocked_users_data:
        users_data[user_id] = blocked_users_data[user_id]
        del blocked_users_data[user_id]
        save_data(USERS_FILE, users_data)
        save_blocked_users()
        bot.send_message(message.chat.id, f"Пользователь {user_id} разблокирован.")
    else:
        bot.send_message(message.chat.id, "Пользователь не найден или не заблокирован.")
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=user_management(message))


@bot.message_handler(func=lambda message: message.text == "📋 Список разблокированных пользователей")
def list_unblocked_users(message):
    if str(message.chat.id) == ADMIN_ID:
        if blocked_users_data:
            blocked_users_list = "\n".join(blocked_users_data.keys())
            bot.send_message(message.chat.id, f"Заблокированные пользователи:\n{blocked_users_list}")
        else:
            bot.send_message(message.chat.id, "Нет заблокированных пользователей.")
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=user_management(message))


@bot.message_handler(func=lambda message: message.text == "🔙 Назад")
def go_back_from_admin(message):
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=main_keyboard(message.chat.id))

@bot.message_handler(func=lambda message: message.text == "🔒 Блокировка пользователей")
def block_users(message):
    if str(message.chat.id) == ADMIN_ID:
        bot.send_message(message.chat.id, "Введите ID пользователя для блокировки:")
        bot.register_next_step_handler(message, block_user)

@bot.message_handler(func=lambda message: message.text == "📊 Статистика")
def show_statistics(message):
    if str(message.chat.id) == ADMIN_ID:
        total_users, total_balance = get_stats()
        stats_text = (
            f"👥 Всего пользователей: {total_users}\n"
            f"💰 Общий баланс: {total_balance:.2f} рублей"
        )
        bot.send_message(message.chat.id, stats_text)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к статистике.")

@bot.message_handler(func=lambda message: message.text == "🔒 Управление пользователями")
def user_management(message):
    if str(message.chat.id) == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("🔍 Найти пользователя"))
        markup.add(types.KeyboardButton("🔒 Заблокированные пользователи"))
        markup.add(types.KeyboardButton("🔙 Назад"))
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к управлению пользователями.")

@bot.message_handler(func=lambda message: message.text == "🔍 Найти пользователя")
def find_user(message):
    if str(message.chat.id) == ADMIN_ID:
        bot.send_message(message.chat.id, "Введите ID пользователя для поиска:")
        bot.register_next_step_handler(message, search_user_by_id)

def search_user_by_id(message):
    user_id = message.text.strip()
    user_data = users_data.get(user_id, None)
    if user_data:
        profile_text = (
            f"🆔 ID пользователя: {user_id}\n"
            f"💰 Баланс: {user_data['balance']:.2f} рублей\n"
            f"🪙 Всего токенов загружено: {user_data['total_tokens']}\n"
            "🔒 Вы можете заблокировать или разблокировать пользователя ниже."
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🚫 Заблокировать", callback_data=f"block_{user_id}"))
        markup.add(types.InlineKeyboardButton("🔓 Разблокировать", callback_data=f"unblock_{user_id}"))
        bot.send_message(message.chat.id, profile_text, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Пользователь не найден.")

def get_stats():
    total_users = len(users_data)
    total_balance = sum(user['balance'] for user in users_data.values())
    return total_users, total_balance

def block_user(user_id, reason):
    if user_id in users_data:
        blocked_users_data[user_id] = reason
        save_blocked_users()
        del users_data[user_id]
        save_data(USERS_FILE, users_data)
        bot.send_message(ADMIN_ID, f"Пользователь {user_id} заблокирован по причине: {reason}.")
    else:
        bot.send_message(ADMIN_ID, f"Пользователь {user_id} не найден.")

def unblock_user(user_id):
    if user_id in blocked_users_data:
        users_data[user_id] = {
            'balance': 0.0,
            'tokens': [],
            'total_tokens': 0,
            'accepted_rules': False
        }
        save_data(USERS_FILE, users_data)
        del blocked_users_data[user_id]
        save_blocked_users()
        bot.send_message(ADMIN_ID, f"Пользователь {user_id} разблокирован.")
    else:
        bot.send_message(ADMIN_ID, f"Пользователь {user_id} не найден среди заблокированных.")

@bot.message_handler(func=lambda message: message.text == "🔒 Заблокированные пользователи")
def show_blocked_users(message):
    if str(message.chat.id) == ADMIN_ID:
        if blocked_users_data:
            blocked_list = "\n".join(f"🆔 {user_id} - Причина: {reason}" for user_id, reason in blocked_users_data.items())
            bot.send_message(message.chat.id, f"🔒 Заблокированные пользователи:\n{blocked_list}")
        else:
            bot.send_message(message.chat.id, "Нет заблокированных пользователей.")
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к заблокированным пользователям.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("block_"))
def block_user_callback(call):
    _, user_id = call.data.split("_")
    bot.send_message(call.message.chat.id, f"Введите причину блокировки для пользователя {user_id}:")
    bot.register_next_step_handler(call.message, lambda msg: block_user(user_id, msg.text))

def unblock_user(call):
    user_id = call.data.split("_")[1]
    if user_id in blocked_users_data:
        del blocked_users_data[user_id]
        save_blocked_users()
        bot.send_message(call.message.chat.id, f"Пользователь {user_id} разблокирован.")
        log_message(f"#Разблокировка{user_id} Пользователь {user_id} разблокирован.")
    else:
        bot.send_message(call.message.chat.id, "Пользователь не найден в списке заблокированных.")
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda message: message.text == "🔒 Блокировка пользователей")
def block_users(message):
    if str(message.chat.id) == ADMIN_ID:
        bot.send_message(message.chat.id, "Введите ID пользователя для блокировки:")
        bot.register_next_step_handler(message, block_user)

def block_user(message):
    user_id = message.text.strip()
    if user_id in users_data:
        blocked_users_data[user_id] = users_data[user_id]
        save_blocked_users()
        bot.send_message(message.chat.id, f"Пользователь {user_id} заблокирован.")
        log_message(f"#Блокировка{user_id} Пользователь {user_id} заблокирован.")
    else:
        bot.send_message(message.chat.id, "Пользователь с таким ID не найден.")

@bot.message_handler(func=lambda message: message.text == "🔓 Разблокировка пользователей")
def unblock_users(message):
    if str(message.chat.id) == ADMIN_ID:
        bot.send_message(message.chat.id, "Введите ID пользователя для разблокировки:")
        bot.register_next_step_handler(message, confirm_unblock_user)

def confirm_unblock_user(message):
    user_id = message.text.strip()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Да", callback_data=f"unblock_{user_id}"))
    markup.add(types.InlineKeyboardButton("❌ Нет", callback_data="cancel_unblock"))
    bot.send_message(message.chat.id, f"Вы действительно хотите разблокировать пользователя {user_id}?", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "🗨 Рассылка")
def mailing_options(message):
    if str(message.chat.id) == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Рассылка с фото"))
        markup.add(types.KeyboardButton("Рассылка без фото"))
        markup.add(types.KeyboardButton("🔙 Назад"))
        bot.send_message(message.chat.id, "Выберите тип рассылки:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к админке.")


def handle_mailing(message, with_photo=False):
    bot.send_message(message.chat.id, "Введите текст сообщения для рассылки:")
    bot.register_next_step_handler(message, lambda msg: collect_message(msg, with_photo))

def collect_message(message, with_photo):
    user_id = str(message.chat.id)
    text = message.text
    if with_photo:
        bot.send_message(user_id, "Теперь отправьте фото для рассылки:")
        bot.register_next_step_handler(message, lambda msg: collect_photo(msg, text))
    else:
        send_mailing(text)

def collect_photo(message, text):
    if message.content_type == 'photo':
        file_info = bot.get_file(message.photo[-1].file_id)
        file = bot.download_file(file_info.file_path)
        with open('temp_photo.jpg', 'wb') as f:
            f.write(file)
        send_mailing(text, photo_path='temp_photo.jpg')
        os.remove('temp_photo.jpg')
    else:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте фото для рассылки.")
        bot.register_next_step_handler(message, lambda msg: collect_photo(msg, text))

def send_mailing(text, photo_path=None):
    user_ids = load_data(USERS_FILE).keys()  # Получаем всех пользователей
    for user_id in user_ids:
        try:
            if photo_path:
                with open(photo_path, 'rb') as photo:
                    bot.send_photo(user_id, photo, caption=text)
            else:
                bot.send_message(user_id, text)
            time.sleep(1)  # Добавляем задержку между сообщениями
        except Exception as e:
            bot.send_message(ADMIN_ID, f"Ошибка при отправке сообщения пользователю {user_id}: {e}")


@bot.message_handler(func=lambda message: message.text == "Рассылка с фото")
def mailing_with_photo(message):
    if str(message.chat.id) == ADMIN_ID:
        handle_mailing(message, with_photo=True)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к админке.")

@bot.message_handler(func=lambda message: message.text == "Рассылка без фото")
def mailing_without_photo(message):
    if str(message.chat.id) == ADMIN_ID:
        handle_mailing(message, with_photo=False)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к админке.")

@bot.message_handler(func=lambda message: message.text == "🆘 Тех. поддержка")
def support(message):
    bot.send_message(message.chat.id, f"Свяжитесь с технической поддержкой: {SUPPORT_BOT_LINK}")

@bot.message_handler(func=lambda message: message.text == "📥 Скачать токены")
def download_tokens_handler(message):
    download_tokens()
    with open('working_tokens.txt', 'rb') as file:
        bot.send_document(message.chat.id, file, caption="Файл с рабочими токенами успешно создан и скачан.")


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
