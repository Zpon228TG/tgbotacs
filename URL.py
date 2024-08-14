import telebot
import json
import random
import string
import os
import subprocess
from telebot import types

# Токен вашего бота и ваш Telegram ID
TOKEN = '7375465921:AAFxiuhZ6YlTTZVcjwKFUhJA7XUPfM9oLyY'
ADMIN_ID = 6578018656

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Имя файлов для хранения данных
JSON_FILE = 'urls.json'
PINNED_FILE = 'pinned.json'
TOPICS_FILE = 'topics.json'

# Функция для генерации случайного ID
def generate_id(length=5):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Функция для загрузки данных из JSON-файла
def load_data(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, 'r') as file:
        return json.load(file)

# Функция для сохранения данных в JSON-файл
def save_data(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

# Функция для отправки последней базы данных
def send_latest_database(message):
    with open(JSON_FILE, 'rb') as file:
        bot.send_document(message.chat.id, file)

# Функция для отправки сводки перед остановкой
def send_summary_before_stop():
    with open(JSON_FILE, 'rb') as file:
        bot.send_document(ADMIN_ID, file, caption="База данных перед остановкой.")

# Функция для перезапуска бота
def restart_bot():
    subprocess.Popen(['python', 'bot.py'])

# Главное меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_manage = types.KeyboardButton("🔧 Управление URL")
    btn_search_manage = types.KeyboardButton("🔍 Поиск и удаление")
    btn_pinned_data = types.KeyboardButton("📌 Закрепленные и база данных")
    btn_stats = types.KeyboardButton("📊 Статистика")
    btn_exit = types.KeyboardButton("🚪 Выход")
    markup.add(btn_manage, btn_search_manage, btn_pinned_data, btn_stats, btn_exit)
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

    if message.text == "🔧 Управление URL":
        manage_urls(message)
    elif message.text == "🔍 Поиск и удаление":
        search_and_delete(message)
    elif message.text == "📌 Закрепленные и база данных":
        pinned_and_database(message)
    elif message.text == "📊 Статистика":
        show_statistics(message)
    elif message.text == "🚪 Выход":
        send_latest_database(message)
        bot.send_message(message.chat.id, "Бот остановлен.")
        send_summary_before_stop()
        restart_bot()
    else:
        bot.reply_to(message, "❓ Пожалуйста, выберите действие из меню.", reply_markup=main_menu())

def manage_urls(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_add = types.KeyboardButton("➕ Добавить URL")
    btn_view = types.KeyboardButton("📄 Просмотреть URL")
    btn_view_topics = types.KeyboardButton("📋 Посмотреть темы")
    markup.add(btn_add, btn_view, btn_view_topics)
    msg = bot.reply_to(message, "Выберите действие:", reply_markup=markup)
    bot.register_next_step_handler(msg, handle_manage_urls)

def handle_manage_urls(message):
    if message.text == "➕ Добавить URL":
        msg = bot.reply_to(message, "📎 Введите URL:")
        bot.register_next_step_handler(msg, process_url)
    elif message.text == "📄 Просмотреть URL":
        view_urls(message)
    elif message.text == "📋 Посмотреть темы":
        view_topics(message)
    else:
        bot.reply_to(message, "❓ Пожалуйста, выберите действие из меню.", reply_markup=main_menu())

def process_url(message):
    url = message.text
    data = load_data(JSON_FILE)

    # Проверка на существование URL в базе
    for url_id, info in data.items():
        if info['url'] == url:
            response = f"❌ Этот URL уже существует в базе:\n\nID: {url_id}\nURL: {info['url']}\nОписание: {info['description']}\nТема(ы): {', '.join(info['topics'])}"
            bot.reply_to(message, response)
            return

    url_id = generate_id()
    msg = bot.reply_to(message, "✍️ Введите описание для URL:")
    bot.register_next_step_handler(msg, process_description, url_id, url)

def process_description(message, url_id, url):
    description = message.text
    msg = bot.reply_to(message, "✍️ Введите тему для URL (можете указать несколько через запятую):")
    bot.register_next_step_handler(msg, process_topics, url_id, url, description)

def process_topics(message, url_id, url, description):
    topics = [topic.strip() for topic in message.text.split(',')]
    save_url(url_id, url, description, topics)
    ask_to_pin(message, url_id, url, description, topics)

    # Отправка последней базы данных после добавления URL
    send_latest_database(message)

def save_url(url_id, url, description, topics):
    data = load_data(JSON_FILE)
    data[url_id] = {"url": url, "description": description, "topics": topics}
    save_data(JSON_FILE, data)

    # Добавление темы в список тем
    topics_data = load_data(TOPICS_FILE)
    for topic in topics:
        if topic not in topics_data:
            topics_data[topic] = []
        if url_id not in topics_data[topic]:
            topics_data[topic].append(url_id)
    save_data(TOPICS_FILE, topics_data)

def ask_to_pin(message, url_id, url, description, topics):
    markup = types.InlineKeyboardMarkup()
    btn_pin_yes = types.InlineKeyboardButton("📌 Закрепить", callback_data=f"pin_{url_id}")
    btn_pin_no = types.InlineKeyboardButton("❌ Не закреплять", callback_data=f"no_pin_{url_id}")
    markup.add(btn_pin_yes, btn_pin_no)
    bot.reply_to(message, f"✅ URL добавлен:\n\nID: {url_id}\nURL: {url}\nОписание: {description}\nТема(ы): {', '.join(topics)}\nЗакрепить?", reply_markup=markup)

def search_and_delete(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_search = types.KeyboardButton("🔍 Поиск URL/ID")
    btn_search_topics = types.KeyboardButton("🔍 Поиск по темам")
    btn_delete = types.KeyboardButton("❌ Удалить URL")
    btn_unpin = types.KeyboardButton("🔓 Открепить URL")
    markup.add(btn_search, btn_search_topics, btn_delete, btn_unpin)
    msg = bot.reply_to(message, "Выберите действие:", reply_markup=markup)
    bot.register_next_step_handler(msg, handle_search_and_delete)

def handle_search_and_delete(message):
    if message.text == "🔍 Поиск URL/ID":
        msg = bot.reply_to(message, "🔍 Введите URL или ID для поиска:")
        bot.register_next_step_handler(msg, process_search)
    elif message.text == "🔍 Поиск по темам":
        msg = bot.reply_to(message, "✍️ Введите тему для поиска:")
        bot.register_next_step_handler(msg, process_search_topics)
    elif message.text == "❌ Удалить URL":
        msg = bot.reply_to(message, "❌ Введите ID URL для удаления:")
        bot.register_next_step_handler(msg, process_deletion)
    elif message.text == "🔓 Открепить URL":
        view_pinned_for_unpin(message)
    else:
        bot.reply_to(message, "❓ Пожалуйста, выберите действие из меню.", reply_markup=main_menu())

def pinned_and_database(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_pinned = types.KeyboardButton("📌 Закрепленные URL")
    btn_download = types.KeyboardButton("📥 Скачать базу данных")
    markup.add(btn_pinned, btn_download)
    msg = bot.reply_to(message, "Выберите действие:", reply_markup=markup)
    bot.register_next_step_handler(msg, handle_pinned_and_database)

def handle_pinned_and_database(message):
    if message.text == "📌 Закрепленные URL":
        view_pinned(message)
    elif message.text == "📥 Скачать базу данных":
        send_latest_database(message)
    else:
        bot.reply_to(message, "❓ Пожалуйста, выберите действие из меню.", reply_markup=main_menu())

def view_pinned(message):
    pinned_data = load_data(PINNED_FILE)
    if not pinned_data:
        bot.reply_to(message, "📌 Нет закрепленных URL.")
        return

    response = "\n\n".join([f"ID: {url_id}\nURL: {info['url']}\nОписание: {info['description']}" for url_id, info in pinned_data.items()])

    markup = types.InlineKeyboardMarkup()
    for url_id in pinned_data:
        btn_unpin = types.InlineKeyboardButton(f"🔓 Открепить ID {url_id}", callback_data=f"unpin_{url_id}")
        markup.add(btn_unpin)

    bot.reply_to(message, response, reply_markup=markup)

def view_pinned_for_unpin(message):
    pinned_data = load_data(PINNED_FILE)
    if not pinned_data:
        bot.reply_to(message, "📌 Нет закрепленных URL.")
        return

    response = "\n\n".join([f"ID: {url_id}\nURL: {info['url']}\nОписание: {info['description']}" for url_id, info in pinned_data.items()])

    markup = types.InlineKeyboardMarkup()
    for url_id in pinned_data:
        btn_unpin = types.InlineKeyboardButton(f"🔓 Открепить ID {url_id}", callback_data=f"unpin_{url_id}")
        markup.add(btn_unpin)

    bot.reply_to(message, response, reply_markup=markup)

def view_urls(message):
    data = load_data(JSON_FILE)
    if not data:
        bot.reply_to(message, "📄 Нет URL в базе данных.")
        return

    response = "\n\n".join([f"ID: {url_id}\nURL: {info['url']}\nОписание: {info['description']}" for url_id, info in data.items()])
    bot.reply_to(message, response)

def view_topics(message):
    topics_data = load_data(TOPICS_FILE)
    if not topics_data:
        bot.reply_to(message, "📋 Нет тем в базе данных.")
        return

    response = "\n\n".join([f"Тема: {topic}\nURL-ы: {', '.join(urls)}" for topic, urls in topics_data.items()])
    bot.reply_to(message, response)

def process_search(message):
    search_term = message.text
    data = load_data(JSON_FILE)
    result = {url_id: info for url_id, info in data.items() if search_term in url_id or search_term in info['url']}
    
    if not result:
        bot.reply_to(message, "🔍 По запросу ничего не найдено.")
        return

    response = "\n\n".join([f"ID: {url_id}\nURL: {info['url']}\nОписание: {info['description']}" for url_id, info in result.items()])
    bot.reply_to(message, response)

def process_search_topics(message):
    topic = message.text
    topics_data = load_data(TOPICS_FILE)
    if topic not in topics_data:
        bot.reply_to(message, "🔍 По запросу ничего не найдено.")
        return

    result = topics_data[topic]
    if not result:
        bot.reply_to(message, "🔍 По запросу ничего не найдено.")
        return

    data = load_data(JSON_FILE)
    response = "\n\n".join([f"ID: {url_id}\nURL: {data[url_id]['url']}\nОписание: {data[url_id]['description']}" for url_id in result])
    bot.reply_to(message, response)

def process_deletion(message):
    url_id = message.text
    data = load_data(JSON_FILE)
    if url_id not in data:
        bot.reply_to(message, "❌ URL с таким ID не найден.")
        return

    del data[url_id]
    save_data(JSON_FILE, data)

    topics_data = load_data(TOPICS_FILE)
    for topic in topics_data:
        if url_id in topics_data[topic]:
            topics_data[topic].remove(url_id)
    save_data(TOPICS_FILE, topics_data)

    bot.reply_to(message, "✅ URL удален.")

def process_unpin(message):
    url_id = message.text
    pinned_data = load_data(PINNED_FILE)
    if url_id not in pinned_data:
        bot.reply_to(message, "❌ URL с таким ID не найден.")
        return

    del pinned_data[url_id]
    save_data(PINNED_FILE, pinned_data)

    bot.reply_to(message, "✅ URL откреплен.")

# Обработка callback-запросов
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data.startswith("pin_"):
        url_id = call.data.split("_")[1]
        pin_url(call.message, url_id)
    elif call.data.startswith("unpin_"):
        url_id = call.data.split("_")[1]
        unpin_url(call.message, url_id)
    
def pin_url(message, url_id):
    data = load_data(JSON_FILE)
    if url_id not in data:
        bot.answer_callback_query(callback_query_id=message.id, text="❌ URL с таким ID не найден.")
        return

    pinned_data = load_data(PINNED_FILE)
    pinned_data[url_id] = data[url_id]
    save_data(PINNED_FILE, pinned_data)

    bot.answer_callback_query(callback_query_id=message.id, text="📌 URL закреплен.")

def unpin_url(message, url_id):
    pinned_data = load_data(PINNED_FILE)
    if url_id not in pinned_data:
        bot.answer_callback_query(callback_query_id=message.id, text="❌ URL с таким ID не найден.")
        return

    del pinned_data[url_id]
    save_data(PINNED_FILE, pinned_data)

    bot.answer_callback_query(callback_query_id=message.id, text="🔓 URL откреплен.")

def show_statistics(message):
    data = load_data(JSON_FILE)
    pinned_data = load_data(PINNED_FILE)
    topics_data = load_data(TOPICS_FILE)

    total_urls = len(data)
    total_pinned = len(pinned_data)
    total_topics = len(topics_data)

    response = (
        f"📊 Статистика:\n\n"
        f"🔗 Всего URL: {total_urls}\n"
        f"📌 Закрепленных URL: {total_pinned}\n"
        f"📚 Тем: {total_topics}"
    )
    bot.reply_to(message, response)


def send_summary_before_stop():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'rb') as file:
            bot.send_document(ADMIN_ID, file, caption="Последняя база данных перед остановкой бота.")

def restart_bot():
    subprocess.Popen(['python3', os.path.realpath(__file__)])
# Запуск бота
bot.polling(none_stop=True)
