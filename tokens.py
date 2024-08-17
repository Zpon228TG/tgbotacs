import telebot
import json
import os
import time

# Инициализация бота
ADMIN_ID = 6578018656  # Замените на ваш Telegram ID
TOKEN = '6417317499:AAETf_TZwTck0dOs7VvEk3ODRz_0jActRs0'  # Замените на токен вашего бота
bot = telebot.TeleBot(TOKEN)

# Файл для хранения токенов
TOKENS_FILE = 'tokens.json'

# Проверка, существует ли файл, если нет, то создаем пустой файл
if not os.path.exists(TOKENS_FILE):
    with open(TOKENS_FILE, 'w') as file:
        json.dump([], file)

# Функция для чтения токенов из файла
def read_tokens():
    with open(TOKENS_FILE, 'r') as file:
        return json.load(file)

# Функция для записи токенов в файл
def write_tokens(tokens):
    with open(TOKENS_FILE, 'w') as file:
        json.dump(tokens, file, indent=4)

# Функция для создания txt файла с токенами
def create_tokens_txt():
    tokens = read_tokens()
    file_path = 'tokens.txt'
    with open(file_path, 'w') as file:
        file.write("\n".join(tokens))
    return file_path

# Команда /start для приветствия и меню
@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == ADMIN_ID:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('➕ Добавить токены', '📋 Посмотреть токены')
        markup.add('❌ Удалить токен', '📊 Статистика')
        markup.add('🗑️ Удалить все токены', '💾 Скачать токены')
        markup.add('📥 Загрузить токены из файла')  # Добавляем новую кнопку
        bot.send_message(message.chat.id, "Привет! Выберите действие:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этому боту.")

# Обработчик для добавления токенов
@bot.message_handler(regexp="➕ Добавить токены")
def add_tokens(message):
    bot.send_message(message.chat.id, "Отправьте мне список токенов для добавления (каждый с новой строки):")
    bot.register_next_step_handler(message, save_tokens)

def save_tokens(message):
    new_tokens = message.text.strip().splitlines()  # Разбиваем текст на отдельные строки
    tokens = read_tokens()
    added_tokens = []

    for token in new_tokens:
        token = token.strip()
        if token and token not in tokens:
            tokens.append(token)
            added_tokens.append(token)

    write_tokens(tokens)

    if added_tokens:
        bot.send_message(message.chat.id, f"✅ Успешно добавлены токены:\n" + "\n".join(added_tokens))
    else:
        bot.send_message(message.chat.id, "⚠️ Все отправленные токены уже были добавлены ранее.")

# Обработчик для просмотра всех токенов
@bot.message_handler(regexp="📋 Посмотреть токены")
def view_tokens(message):
    tokens = read_tokens()
    if tokens:
        bot.send_message(message.chat.id, "📋 Список токенов:\n" + "\n".join(tokens))
    else:
        bot.send_message(message.chat.id, "📭 Список токенов пуст.")

# Функция для перезапуска бота
def restart_bot():
    subprocess.Popen(['python', 'bot.py'])

# Обработчик для удаления токена
@bot.message_handler(regexp="❌ Удалить токен")
def delete_token(message):
    tokens = read_tokens()
    if tokens:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        for token in tokens:
            markup.add(token)
        markup.add("❌ Отмена")
        bot.send_message(message.chat.id, "Выберите токен для удаления:", reply_markup=markup)
        bot.register_next_step_handler(message, confirm_delete_token)
    else:
        bot.send_message(message.chat.id, "📭 Список токенов пуст.")

def confirm_delete_token(message):
    selected_token = message.text.strip()
    tokens = read_tokens()

    if selected_token in tokens:
        tokens.remove(selected_token)
        write_tokens(tokens)
        bot.send_message(message.chat.id, "✅ Токен успешно удален!")
    elif selected_token == "❌ Отмена":
        bot.send_message(message.chat.id, "Удаление отменено.")
    else:
        bot.send_message(message.chat.id, "⚠️ Токен не найден.")

# Обработчик для удаления всех токенов
@bot.message_handler(regexp="🗑️ Удалить все токены")
def delete_all_tokens(message):
    if message.from_user.id == ADMIN_ID:
        write_tokens([])
        bot.send_message(message.chat.id, "🗑️ Все токены были успешно удалены.")
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этому боту.")

# Обработчик для просмотра статистики
@bot.message_handler(regexp="📊 Статистика")
def show_statistics(message):
    tokens = read_tokens()
    total_tokens = len(tokens)
    bot.send_message(message.chat.id, f"📊 Статистика:\nВсего токенов: {total_tokens}")

# Обработчик для скачивания токенов в txt
@bot.message_handler(regexp="💾 Скачать токены")
def download_tokens(message):
    if message.from_user.id == ADMIN_ID:
        file_path = create_tokens_txt()
        with open(file_path, 'rb') as file:
            bot.send_document(message.chat.id, file)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этому боту.")

# Обработчик для загрузки токенов из файла
@bot.message_handler(regexp="📥 Загрузить токены из файла")
def request_file(message):
    bot.send_message(message.chat.id, "Отправьте мне файл с токенами (.txt):")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    if message.from_user.id == ADMIN_ID:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Преобразование содержимого файла в строку
        file_content = downloaded_file.decode('utf-8')
        tokens_from_file = file_content.splitlines()
        
        # Загрузка текущих токенов
        existing_tokens = read_tokens()
        existing_tokens_set = set(existing_tokens)
        
        # Проверка новых токенов и их добавление
        new_tokens = set(tokens_from_file) - existing_tokens_set
        if new_tokens:
            existing_tokens.extend(new_tokens)
            write_tokens(existing_tokens)
            bot.send_message(message.chat.id, f"✅ Добавлено {len(new_tokens)} новых токенов. Всего токенов: {len(existing_tokens)}.")
        else:
            bot.send_message(message.chat.id, "⚠️ Все токены из файла уже были добавлены ранее.")
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этому боту.")

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
