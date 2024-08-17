import os
import json
import subprocess
import telebot
from telebot import types

# Токен вашего бота и ваш Telegram ID
TOKEN = '7375465921:AAFxiuhZ6YlTTZVcjwKFUhJA7XUPfM9oLyY'
ADMIN_ID = 6578018656

# Список директорий для поиска ботов
BOT_DIRECTORIES = [
    '/data/data/com.termux/files/home/tgbotacs/code',
    '/data/data/com.termux/files/home/tgbotacs'
]

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Функция для отображения главного меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_run_code = types.KeyboardButton("📝 Запустить Python файл")
    btn_manage_bots = types.KeyboardButton("💻 Управление ботами")
    btn_execute_command = types.KeyboardButton("💻 Выполнить команду")
    markup.add(btn_run_code, btn_manage_bots, btn_execute_command)
    return markup

# Функция для управления ботами
def manage_bots_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_add_bot = types.KeyboardButton("➕ Добавить бота")
    btn_remove_bot = types.KeyboardButton("❌ Удалить бота")
    btn_start_all_bots = types.KeyboardButton("🚀 Запустить всех ботов")
    btn_stop_all_bots = types.KeyboardButton("🛑 Остановить всех ботов")
    markup.add(btn_add_bot, btn_remove_bot, btn_start_all_bots, btn_stop_all_bots)
    return markup

# Функция для поиска файла по названию
def find_file_by_name(filename):
    for directory in BOT_DIRECTORIES:
        potential_path = os.path.join(directory, filename)
        if os.path.isfile(potential_path):
            return potential_path, directory
    return None, None

# Функция для добавления бота
def process_add_bot(message):
    bot_name = message.text.strip()
    if not bot_name:
        bot.reply_to(message, "❌ Название бота не может быть пустым.")
        return

    bot_path, directory = find_file_by_name(bot_name + '.py')
    if bot_path is None:
        bot.reply_to(message, f"❌ Бот с таким названием не найден в указанных директориях.\nИщем в следующих директориях:\n{', '.join(BOT_DIRECTORIES)}")
        return

    bots = load_data('bots.json')
    if bot_name in bots:
        bot.reply_to(message, "❌ Бот с таким названием уже существует.")
        return

    bots[bot_name] = {'path': bot_path, 'status': 'stopped'}
    save_data('bots.json', bots)
    bot.reply_to(message, f"✅ Бот '{bot_name}' добавлен.")

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

    if message.text == "📝 Запустить Python файл":
        msg = bot.reply_to(message, "✍️ Введите команду для запуска Python файла:")
        bot.register_next_step_handler(msg, process_run_python)

    elif message.text == "💻 Управление ботами":
        bot.reply_to(message, "💻 Выберите действие:", reply_markup=manage_bots_menu())

    elif message.text == "➕ Добавить бота":
        msg = bot.reply_to(message, "✍️ Введите название бота (например: bot_name):")
        bot.register_next_step_handler(msg, process_add_bot)

    elif message.text == "❌ Удалить бота":
        msg = bot.reply_to(message, "✍️ Введите название бота для удаления:")
        bot.register_next_step_handler(msg, process_remove_bot)

    elif message.text == "🚀 Запустить всех ботов":
        start_all_bots(message)

    elif message.text == "🛑 Остановить всех ботов":
        stop_all_bots(message)

    elif message.text == "💻 Выполнить команду":
        msg = bot.reply_to(message, "✍️ Введите команду для выполнения:")
        bot.register_next_step_handler(msg, process_execute_command)

    else:
        bot.reply_to(message, "❓ Пожалуйста, выберите действие из меню.", reply_markup=main_menu())

# Обработка команды для запуска Python файла
def process_run_python(message):
    command = message.text.strip()
    bot_path, _ = find_file_by_name(command)
    if bot_path is None:
        bot.reply_to(message, "❌ Файл не найден.")
        return

    result = execute_command(f"python {bot_path}")
    if "Error" in result:
        bot.reply_to(message, f"❌ Ошибка при выполнении:\n{result}")
    else:
        bot.reply_to(message, f"✅ Успешное выполнение:\n{result}")

# Обработка команды для выполнения произвольной команды
def process_execute_command(message):
    command = message.text.strip()
    result = execute_command(command)
    if "Error" in result:
        bot.reply_to(message, f"❌ Ошибка при выполнении:\n{result}")
    else:
        bot.reply_to(message, f"✅ Успешное выполнение:\n{result}")

# Обработка команды для удаления бота
def process_remove_bot(message):
    bot_name = message.text.strip()
    bots = load_data('bots.json')
    if bot_name in bots:
        del bots[bot_name]
        save_data('bots.json', bots)
        bot.reply_to(message, f"✅ Бот '{bot_name}' удален.")
    else:
        bot.reply_to(message, "❌ Бот с таким названием не найден.")

# Запуск всех ботов
def start_all_bots(message):
    bots = load_data('bots.json')
    results = []
    for bot_name, bot_info in bots.items():
        if isinstance(bot_info, dict):
            if bot_info.get('status') == 'running':
                results.append(f"Бот '{bot_name}' уже запущен.")
                continue

            try:
                subprocess.Popen(['python', bot_info['path']], cwd=os.path.dirname(bot_info['path']))
                bots[bot_name]['status'] = 'running'
                results.append(f"Бот '{bot_name}' успешно запущен.")
            except Exception as e:
                results.append(f"Не удалось запустить '{bot_name}': {str(e)}")
        else:
            results.append(f"Ошибка: данные о боте '{bot_name}' некорректны.")

    save_data('bots.json', bots)
    bot.reply_to(message, "\n".join(results))

# Остановка всех ботов
def stop_all_bots(message):
    bots = load_data('bots.json')
    results = []
    for bot_name, bot_info in bots.items():
        if isinstance(bot_info, dict):
            if bot_info.get('status') == 'stopped':
                results.append(f"Бот '{bot_name}' уже остановлен.")
                continue

            try:
                # Здесь необходимо остановить бот, если возможно
                # Это может потребовать дополнительного механизма для отслеживания и управления процессами
                bots[bot_name]['status'] = 'stopped'
                results.append(f"Бот '{bot_name}' успешно остановлен.")
            except Exception as e:
                results.append(f"Не удалось остановить '{bot_name}': {str(e)}")
        else:
            results.append(f"Ошибка: данные о боте '{bot_name}' некорректны.")

    save_data('bots.json', bots)
    bot.reply_to(message, "\n".join(results))

# Загрузка данных из JSON файла
def load_data(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, 'r') as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return {}  # Если файл пуст или некорректен, возвращаем пустой словарь

# Сохранение данных в JSON файл
def save_data(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

# Выполнение команды в терминале
def execute_command(command):
    try:
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
        return result
    except subprocess.CalledProcessError as e:
        return f"Ошибка: {e.output}"

# Основной цикл обработки сообщений
bot.polling(none_stop=True, timeout=60)
