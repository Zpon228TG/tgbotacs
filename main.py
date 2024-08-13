import telebot
import json
import os
import random

# Токен вашего бота и ваш Telegram ID
bot = telebot.TeleBot("7264644656:AAEXeOL9SV0W-ykoOicic6Ec-9uaDHgg-6k")
admin_id = 6578018656

# Файлы для хранения данных
accounts_file = 'accounts.json'
gift_accounts_file = 'gift_accounts.json'

# Создаем файлы, если они не существуют
for file in [accounts_file, gift_accounts_file]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump({}, f)

# Функция для проверки, является ли пользователь администратором
def is_admin(message):
    return message.from_user.id == admin_id

# Команда старт
@bot.message_handler(commands=['start'])
def start(message):
    if not is_admin(message):
        bot.reply_to(message, "⛔️ Вам не разрешено использовать этого бота.")
        return

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("➕ Добавить аккаунты")
    markup.row("📂 Показать папки")
    markup.row("📊 Статистика")
    markup.row("🎁 Подарочные аккаунты")
    bot.send_message(message.chat.id, "🔐 Добро пожаловать! Выберите действие:", reply_markup=markup)

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if not is_admin(message):
        bot.reply_to(message, "⛔️ Вам не разрешено использовать этого бота.")
        return
    
    if message.text == "➕ Добавить аккаунты":
        bot.send_message(message.chat.id, "Сколько аккаунтов вы хотите добавить? (от 1 до 100)")
        bot.register_next_step_handler(message, get_accounts_count)
    elif message.text == "📂 Показать папки":
        show_folders(message)
    elif message.text == "📊 Статистика":
        show_statistics(message)
    elif message.text == "🎁 Подарочные аккаунты":
        handle_gift_accounts(message)
    elif message.text == "🔙 Назад":
        start(message)
    else:
        bot.send_message(message.chat.id, "❗ Пожалуйста, выберите действие из меню.")

def get_accounts_count(message):
    try:
        count = int(message.text)
        if count < 1 or count > 100:
            bot.send_message(message.chat.id, "❗ Пожалуйста, введите число от 1 до 100.")
            bot.register_next_step_handler(message, get_accounts_count)
            return
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("🎁 Добавить подарок")
        markup.row("❌ Не добавлять подарок")
        markup.row("🔙 Назад")
        bot.send_message(message.chat.id, "🎁 Добавлять подарок? Выберите действие:", reply_markup=markup)
        bot.register_next_step_handler(message, add_gift_option, count)
    except ValueError:
        bot.send_message(message.chat.id, "❗ Пожалуйста, введите число.")
        bot.register_next_step_handler(message, get_accounts_count)


def add_gift_option(message, count):
    if message.text == "🎁 Добавить подарок":
        bot.send_message(message.chat.id, "🔑 Введите логин для первого аккаунта:")
        bot.register_next_step_handler(message, get_login, count, True, [])
    elif message.text == "❌ Не добавлять подарок":
        bot.send_message(message.chat.id, "🔑 Введите логин для первого аккаунта:")
        bot.register_next_step_handler(message, get_login, count, False, [])
    elif message.text == "🔙 Назад":
        start(message)
    else:
        bot.send_message(message.chat.id, "❗ Неверный выбор. Пожалуйста, попробуйте снова.")
        add_gift_option(message, count)


def get_login(message, count, has_gift, accounts):
    login = message.text
    bot.send_message(message.chat.id, "🔑 Введите пароль для этого аккаунта:")
    bot.register_next_step_handler(message, get_password, count, has_gift, accounts, login)

def get_password(message, count, has_gift, accounts, login):
    password = message.text
    accounts.append({'login': login, 'password': password})

    if len(accounts) < count:
        bot.send_message(message.chat.id, f"🔑 Введите логин для аккаунта {len(accounts) + 1}:")
        bot.register_next_step_handler(message, get_login, count, has_gift, accounts)
    else:
        if has_gift:
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("🎁 Добавить подарочный аккаунт из базы данных")
            markup.row("📝 Описание подарка")
            markup.row("🔙 Назад")
            bot.send_message(message.chat.id, "Выберите тип подарка:", reply_markup=markup)
            bot.register_next_step_handler(message, handle_gift_type, accounts)
        else:
            save_accounts(message, accounts, False)


def handle_gift_type(message, accounts):
    if message.text == "🎁 Добавить подарочный аккаунт из базы данных":
        add_gift_account_from_db(message, accounts)
    elif message.text == "📝 Описание подарка":
        bot.send_message(message.chat.id, "📝 Введите описание для подарка:")
        bot.register_next_step_handler(message, get_gift_description, accounts)
    elif message.text == "🔙 Назад":
        start(message)
    else:
        bot.send_message(message.chat.id, "❗ Неверный выбор. Пожалуйста, попробуйте снова.")
        handle_gift_type(message, accounts)




def add_gift_account_from_db(message, accounts):
    with open(gift_accounts_file, 'r') as f:
        gift_data = json.load(f)
    
    if not gift_data:
        bot.send_message(message.chat.id, "❌ Нет доступных подарочных аккаунтов в базе данных.")
        handle_gift_type(message, accounts)
        return
    
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for gift_id in gift_data.keys():
        markup.add(f"📜 Добавить {gift_id}")
    markup.row("🔙 Назад")
    bot.send_message(message.chat.id, "Выберите подарочный аккаунт для добавления:", reply_markup=markup)
    bot.register_next_step_handler(message, add_gift_account_to_task, gift_data, accounts)

def add_gift_account_to_task(message, gift_data, accounts):
    gift_id = message.text.split()[-1]
    if gift_id in gift_data:
        gift_account = gift_data[gift_id]
        accounts.append(gift_account)
        with open(gift_accounts_file, 'r+') as f:
            gift_data = json.load(f)
            del gift_data[gift_id]
            f.seek(0)
            f.truncate()
            json.dump(gift_data, f, indent=4)
        
        save_accounts(message, accounts, True, gift_type='account')
    else:
        bot.send_message(message.chat.id, "❌ Подарочный аккаунт не найден.")
        handle_gift_type(message, accounts)



def get_gift_description(message, accounts):
    description = message.text
    accounts.append({'gift_description': description})
    save_accounts(message, accounts, True)

def save_accounts(message, accounts, has_gift, gift_type=None):
    account_id = str(random.randint(1000, 9999))
    data = {
        'accounts': accounts,
        'gift_description': None
    }

    if has_gift:
        if gift_type == 'description':
            data['gift_description'] = accounts[-1].get('gift_description')
        elif gift_type == 'account':
            gift_account = accounts[-1]
            data['gift_description'] = f'Логин: {gift_account.get("login", "Не указан")}, Пароль: {gift_account.get("password", "Не указан")}'

    with open(accounts_file, 'r+') as f:
        existing_data = json.load(f)
        existing_data[account_id] = data
        f.seek(0)
        f.truncate()
        json.dump(existing_data, f, indent=4)

    bot.send_message(message.chat.id, f"✅ Аккаунты добавлены с ID: {account_id} 🎉")
    start(message)


def show_folders(message):
    with open(accounts_file, 'r') as f:
        data = json.load(f)
    
    if not data:
        bot.send_message(message.chat.id, "❌ Нет добавленных папок.")
        start(message)
        return
    
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for folder_id in data.keys():
        markup.add(f"📂 Папка {folder_id}")
    markup.row("🔙 Назад")
    bot.send_message(message.chat.id, "Выберите папку, чтобы просмотреть:", reply_markup=markup)
    bot.register_next_step_handler(message, view_folder)

def view_folder(message):
    folder_id = message.text.split()[-1]
    with open(accounts_file, 'r') as f:
        data = json.load(f)
    
    if folder_id not in data:
        bot.send_message(message.chat.id, "❌ Папка не найдена.")
        start(message)
        return
    
    folder_data = data[folder_id]
    accounts = folder_data.get('accounts', [])
    gift_description = folder_data.get('gift_description', None)
    
    text = ""

    # Отображаем обычные аккаунты
    if accounts:
        text += "\n".join([f"Логин: {acc.get('login', 'Не указан')}, Пароль: {acc.get('password', 'Не указан')}" for acc in accounts])

    # Отображаем информацию о подарке, если она есть
    if gift_description:
        text += f"\n🎁 Подарок: {gift_description}"
    
    if not accounts and not gift_description:
        text = "❌ Нет данных в этой папке."

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row("🗑️ Удалить папку")
    markup.row("🔙 Назад")
    bot.send_message(message.chat.id, f"🗂️ Содержание папки {folder_id}:\n{text}", reply_markup=markup)
    bot.register_next_step_handler(message, handle_folder_options, folder_id)


def handle_folder_options(message, folder_id):
    if message.text == "🗑️ Удалить папку":
        with open(accounts_file, 'r+') as f:
            data = json.load(f)
            del data[folder_id]
            f.seek(0)
            f.truncate()
            json.dump(data, f, indent=4)
        bot.send_message(message.chat.id, "✅ Папка удалена.")
    elif message.text == "🔙 Назад":
        show_folders(message)
    else:
        bot.send_message(message.chat.id, "❗ Неверный выбор. Пожалуйста, попробуйте снова.")
        handle_folder_options(message, folder_id)

def show_statistics(message):
    with open(accounts_file, 'r') as f:
        data = json.load(f)
    
    total_urls = sum(len(folder.get('accounts', [])) for folder in data.values())
    total_topics = len(data)
    
    text = f"📊 Статистика:\n📁 Папок: {total_topics}\n🔗 Аккаунтов: {total_urls}"
    bot.send_message(message.chat.id, text)
    start(message)

def handle_gift_accounts(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row("🎁 Добавить новый подарок")
    markup.row("📜 Просмотреть подарочные аккаунты")
    markup.row("🔙 Назад")
    bot.send_message(message.chat.id, "Выберите действие для подарочных аккаунтов:", reply_markup=markup)
    bot.register_next_step_handler(message, process_gift_account_action)

def process_gift_account_action(message):
    if message.text == "🎁 Добавить новый подарок":
        bot.send_message(message.chat.id, "🔑 Введите логин подарочного аккаунта:")
        bot.register_next_step_handler(message, add_gift_login)
    elif message.text == "📜 Просмотреть подарочные аккаунты":
        view_gift_accounts(message)
    elif message.text == "🔙 Назад":
        start(message)
    else:
        bot.send_message(message.chat.id, "❗ Неверный выбор. Пожалуйста, попробуйте снова.")
        handle_gift_accounts(message)

def add_gift_login(message):
    login = message.text
    bot.send_message(message.chat.id, "🔑 Введите пароль для подарочного аккаунта:")
    bot.register_next_step_handler(message, add_gift_password, login)

def add_gift_password(message, login):
    password = message.text
    gift_id = str(random.randint(1000, 9999))
    gift_account = {'login': login, 'password': password}
    
    with open(gift_accounts_file, 'r+') as f:
        gift_data = json.load(f)
        gift_data[gift_id] = gift_account
        f.seek(0)
        f.truncate()
        json.dump(gift_data, f, indent=4)
    
    bot.send_message(message.chat.id, f"✅ Подарочный аккаунт добавлен с ID: {gift_id} 🎉")
    handle_gift_accounts(message)

def view_gift_accounts(message):
    with open(gift_accounts_file, 'r') as f:
        data = json.load(f)
    
    if not data:
        bot.send_message(message.chat.id, "❌ Нет подарочных аккаунтов в базе данных.")
        handle_gift_accounts(message)
        return
    
    text = "\n".join([f"📜 ID: {gift_id}, Логин: {info.get('login', 'Не указан')}" for gift_id, info in data.items()])
    bot.send_message(message.chat.id, f"📜 Подарочные аккаунты:\n{text}")
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row("🗑️ Удалить подарок")
    markup.row("🔙 Назад")
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    bot.register_next_step_handler(message, handle_gift_action)

def handle_gift_action(message):
    if message.text == "🗑️ Удалить подарок":
        bot.send_message(message.chat.id, "🔑 Введите ID подарочного аккаунта для удаления:")
        bot.register_next_step_handler(message, delete_gift_account)
    elif message.text == "🔙 Назад":
        handle_gift_accounts(message)
    else:
        bot.send_message(message.chat.id, "❗ Неверный выбор. Пожалуйста, попробуйте снова.")
        handle_gift_action(message)

def delete_gift_account(message):
    gift_id = message.text
    with open(gift_accounts_file, 'r+') as f:
        gift_data = json.load(f)
        if gift_id in gift_data:
            del gift_data[gift_id]
            f.seek(0)
            f.truncate()
            json.dump(gift_data, f, indent=4)
            bot.send_message(message.chat.id, f"✅ Подарочный аккаунт с ID {gift_id} удален.")
        else:
            bot.send_message(message.chat.id, "❌ Подарочный аккаунт не найден.")
    handle_gift_accounts(message)

while True:
    try:
        bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(15) 
