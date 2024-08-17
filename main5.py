import subprocess
import os
import json
import signal
import telebot
from telebot import types

# Токен вашего бота и ваш Telegram ID
TOKEN = '7242149578:AAGoI3qzv5VjL4pAnvqvSjH-WjXbRbFYKe0'
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
    btn_stop_bot = types.KeyboardButton("❌ Остановить выбранного бота")
    btn_running_bots = types.KeyboardButton("📋 Список запущенных ботов")
    markup.add(btn_add_bot, btn_run_python, btn_run_command, btn_start_all, btn_stop_all)
    markup.add(btn_stop_bot, btn_running_bots)
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
        bot.reply_to(message, "✍️ Введите название бота:")
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
    elif message.text == "❌ Остановить выбранного бота":
        list_running_bots(message)
    elif message.text == "📋 Список запущенных ботов":
        show_running_bots(message)
    else:
        bot.reply_to(message, "❓ Пожалуйста, выберите действие из меню.", reply_markup=main_menu())

def add_bot(message):
    bot_name = message.text.strip()
    if not bot_name:
        bot.reply_to(message, "❌ Название бота не может быть пустым.")
        return

    full_path = os.path.join(BOT_DIRECTORY, f'{bot_name}.py')
    if not os.path.isfile(full_path):
        bot.reply_to(message, f"❌ Файл '{full_path}' не найден.")
        return
    
    bots = load_data('bots.json')
    if bot_name in bots:
        bot.reply_to(message, "❌ Бот с таким названием уже существует.")
        return
    
    bots[bot_name] = {
        'path': full_path,
        'status': 'stopped',
        'pid': None  # Изначально PID отсутствует
    }
    save_data('bots.json', bots)
    bot.reply_to(message, f"✅ Бот '{bot_name}' успешно добавлен.")

def run_python_file(message):
    file_path = os.path.join(BOT_DIRECTORY, message.text.strip())
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
    command = message.text.strip()
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
        if isinstance(bot_info, dict):  # Убедитесь, что bot_info - это словарь
            bot_path = bot_info.get('path')
            if bot_path and os.path.isfile(bot_path):
                try:
                    process = subprocess.Popen(['python', bot_path])
                    bot_info['status'] = 'running'
                    bot_info['pid'] = process.pid  # Сохранение PID процесса
                    save_data('bots.json', bots)
                except Exception as e:
                    bot.reply_to(message, f"Ошибка при запуске бота {bot_name}: {e}")
            else:
                bot.reply_to(message, f"❌ Бот {bot_name} с путем {bot_path} не найден.")
        else:
            bot.reply_to(message, f"Ошибка: данные о боте {bot_name} некорректны.")

    bot.reply_to(message, "🚀 Все боты запущены.")

def stop_all_bots(message):
    bots = load_data('bots.json')
    if not bots:
        bot.reply_to(message, "🔍 Нет зарегистрированных ботов для остановки.")
        return

    for bot_name, bot_info in bots.items():
        if isinstance(bot_info, dict) and bot_info.get('status') == 'running':
            pid = bot_info.get('pid')
            if pid:
                try:
                    os.kill(pid, signal.SIGTERM)  # Остановка процесса по PID
                    bot_info['status'] = 'stopped'
                    bot_info['pid'] = None
                    save_data('bots.json', bots)
                    bot.reply_to(message, f"🛑 Бот {bot_name} остановлен.")
                except Exception as e:
                    bot.reply_to(message, f"Ошибка при остановке бота {bot_name}: {e}")
            else:
                bot.reply_to(message, f"❌ PID не найден для бота {bot_name}.")
        else:
            bot.reply_to(message, f"❌ Бот {bot_name} не запущен.")

    bot.reply_to(message, "🛑 Все запущенные боты остановлены.")

def list_running_bots(message):
    bots = load_data('bots.json')
    running_bots = {name: info for name, info in bots.items() if info.get('status') == 'running'}

    if not running_bots:
        bot.reply_to(message, "🔍 Нет запущенных ботов.")
        return

    markup = types.InlineKeyboardMarkup()
    for bot_name in running_bots.keys():
        markup.add(types.InlineKeyboardButton(text=bot_name, callback_data=f'stop_{bot_name}'))
    
    bot.reply_to(message, "📋 Выберите бота для остановки:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('stop_'))
def stop_selected_bot(call):
    bot_name = call.data[len('stop_'):]
    bots = load_data('bots.json')

    if bot_name in bots and bots[bot_name].get('status') == 'running':
        pid = bots[bot_name].get('pid')
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                bots[bot_name]['status'] = 'stopped'
                bots[bot_name]['pid'] = None
                save_data('bots.json', bots)
                bot.answer_callback_query(call.id, f"🛑 Бот {bot_name} остановлен.")
            except Exception as e:
                bot.answer_callback_query(call.id, f"Ошибка при остановке бота {bot_name}: {e}")
        else:
            bot.answer_callback_query(call.id, f"❌ PID не найден для бота {bot_name}.")
    else:
        bot.answer_callback_query(call.id, f"❌ Бот {bot_name} не запущен.")

def show_running_bots(message):
    bots = load_data('bots.json')
    running_bots = {name: info for name, info in bots.items() if info.get('status') == 'running'}

    if not running_bots:
        bot.reply_to(message, "🔍 Нет запущенных ботов.")
        return

    bot_list = '\n'.join(running_bots.keys())
    bot.reply_to(message, f"📋 Запущенные боты:\n{bot_list}")

def load_data(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

bot.polling(none_stop=True)
