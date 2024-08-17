import subprocess
import os
import json
import telebot
from telebot import types

# Токен вашего бота и ваш Telegram ID
TOKEN = '7375465921:AAFxiuhZ6YlTTZVcjwKFUhJA7XUPfM9oLyY'
ADMIN_ID = 6578018656

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Путь к директории, где ищутся боты
BOT_DIRECTORY = '/data/data/com.termux/files/home/tgbotacs/'

# Главное меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_add_bot = types.KeyboardButton("➕ Добавить бота")
    btn_run_python = types.KeyboardButton("📝 Запустить Python файл")
    btn_run_command = types.KeyboardButton("🔧 Выполнить команду")
    btn_start_all = types.KeyboardButton("🚀 Запустить всех ботов")
    btn_stop_all = types.KeyboardButton("🛑 Остановить всех ботов")
    markup.add(btn_add_bot, btn_run_python, btn_run_command, btn_start_all, btn_stop_all)
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

    if message.text == "➕ Добавить бота":
        bot.reply_to(message, "✍️ Введите название бота и путь к его файлу (например: 'bot_name /path/to/bot.py'):")
        bot.register_next_step_handler(message, add_bot)
    elif message.text == "📝 Запустить Python файл":
        bot.reply_to(message, "✍️ Введите команду для запуска Python файла:")
        bot.register_next_step_handler(message, run_python_file)
    elif message.text == "🔧 Выполнить команду":
        bot.reply_to(message, "✍️ Введите команду для выполнения:")
        bot.register_next_step_handler(message, execute_command)
    elif message.text == "🚀 Запустить всех ботов":
        start_all_bots(message)
    elif message.text == "🛑 Остановить всех ботов":
        stop_all_bots(message)
    else:
        bot.reply_to(message, "❓ Пожалуйста, выберите действие из меню.", reply_markup=main_menu())

def add_bot(message):
    try:
        bot_name, bot_path = message.text.split(' ', 1)
        full_path = os.path.join(BOT_DIRECTORY, bot_path)
        if not os.path.isfile(full_path):
            bot.reply_to(message, f"❌ Файл '{full_path}' не найден.")
            return
        
        bots = load_data('bots.json')
        if bot_name in bots:
            bot.reply_to(message, "❌ Бот с таким названием уже существует.")
            return
        
        bots[bot_name] = {
            'path': full_path,
            'status': 'stopped'
        }
        save_data('bots.json', bots)
        bot.reply_to(message, f"✅ Бот '{bot_name}' успешно добавлен.")
    except ValueError:
        bot.reply_to(message, "❌ Неправильный формат. Используйте: название_бота /путь/к/боту.py")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

def run_python_file(message):
    file_path = os.path.join(BOT_DIRECTORY, message.text)
    if not os.path.isfile(file_path):
        bot.reply_to(message, f"❌ Файл '{file_path}' не найден.")
        return
    
    try:
        result = subprocess.run(['python', file_path], capture_output=True, text=True)
        if result.returncode == 0:
            bot.reply_to(message, f"✅ Успешное выполнение:\n{result.stdout}")
        else:
            bot.reply_to(message, f"❌ Ошибка выполнения:\n{result.stderr}")
    except Exception as e:
        bot.reply_to(message, f"Ошибка при выполнении файла: {e}")

def execute_command(message):
    command = message.text
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            bot.reply_to(message, f"✅ Команда выполнена успешно:\n{result.stdout}")
        else:
            bot.reply_to(message, f"❌ Ошибка выполнения команды:\n{result.stderr}")
    except Exception as e:
        bot.reply_to(message, f"Ошибка при выполнении команды: {e}")

def start_all_bots(message):
    bots = load_data('bots.json')
    if not bots:
        bot.reply_to(message, "🔍 Нет зарегистрированных ботов для запуска.")
        return
    
    for bot_name, bot_info in bots.items():
        if 'path' in bot_info:
            bot_path = bot_info['path']
            if os.path.isfile(bot_path):
                try:
                    subprocess.Popen(['python', bot_path])
                    bot_info['status'] = 'running'
                    save_data('bots.json', bots)
                except Exception as e:
                    bot.reply_to(message, f"Ошибка при запуске бота {bot_name}: {e}")
            else:
                bot.reply_to(message, f"❌ Бот {bot_name} с путем {bot_path} не найден.")
        else:
            bot.reply_to(message, f"❌ Данные о боте {bot_name} некорректны.")

    bot.reply_to(message, "🚀 Все боты запущены.")

def stop_all_bots(message):
    bots = load_data('bots.json')
    for bot_name, bot_info in bots.items():
        if bot_info.get('status') == 'running':
            # Здесь нужно реализовать логику для остановки ботов, если это возможно
            bot_info['status'] = 'stopped'
            save_data('bots.json', bots)
            bot.reply_to(message, f"🛑 Бот {bot_name} остановлен.")
    bot.reply_to(message, "🛑 Все запущенные боты остановлены.")

def load_data(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, 'r') as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return {}  # Если файл пуст или некорректен, возвращаем пустой словарь

def save_data(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

# Основной цикл обработки сообщений
bot.polling(none_stop=True, timeout=60)
