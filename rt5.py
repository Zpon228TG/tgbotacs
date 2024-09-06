import telebot
from telebot import types
import json
import datetime
import os

TOKEN = '7053322665:AAFe3nW8Ls3oThVaA1gDXCq7biaaolWe7IA'
ADMIN_ID = 750334025

bot = telebot.TeleBot(TOKEN)

# Файлы для хранения данных
DATA_FILE = 'data.json'
MODERATORS_FILE = 'moderators.json'
BIRTHDAYS_PATH = '.'  # Папка с изображениями именинников в той же директории
SCHEDULE_PHOTO_PATH = '.'  # Папка с изображениями расписания в той же директории

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            'schedule': {},
            'access_list': [],
            'events': [],
            'schedule_photo': None,
            'birthdays': {}  # Убедитесь, что ключ 'birthdays' всегда присутствует
        }
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
        # Добавляем недостающие ключи
        data.setdefault('birthdays', {})
        data.setdefault('schedule', {})
        data.setdefault('access_list', [])
        data.setdefault('events', [])
        data.setdefault('schedule_photo', None)
        return data

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def load_moderators():
    if not os.path.exists(MODERATORS_FILE):
        return [ADMIN_ID]
    with open(MODERATORS_FILE, 'r') as f:
        return json.load(f)

def save_moderators(moderators):
    with open(MODERATORS_FILE, 'w') as f:
        json.dump(moderators, f, indent=4)

# Проверка доступа пользователя
def has_access(user_id):
    data = load_data()
    return user_id in data['access_list'] or user_id == ADMIN_ID

def is_moderator(user_id):
    moderators = load_moderators()
    return user_id in moderators

# Начальное меню
@bot.message_handler(commands=['start'])
def start(message):
    if not has_access(message.from_user.id):
        bot.send_message(message.chat.id, "У вас нет доступа к этому боту.")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('📅 Именинники', '📚 Расписание', '🎉 Мероприятия')
    if is_moderator(message.from_user.id):
        markup.add('👑 Админка')
    bot.send_message(message.chat.id, "Добро пожаловать!", reply_markup=markup)

# Отправка изображения с именинниками
@bot.message_handler(regexp="📅 Именинники")
def birthdays(message):
    if not has_access(message.from_user.id):
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")
        return

    data = load_data()
    month = datetime.datetime.now().strftime("%B").lower()
    file_path = data['birthdays'].get(month)
    if file_path and os.path.exists(file_path):
        bot.send_photo(message.chat.id, open(file_path, 'rb'))
    else:
        bot.send_message(message.chat.id, "Изображение именинников для этого месяца отсутствует.")

# Расписание: выбор формата
@bot.message_handler(regexp="📚 Расписание")
def schedule(message):
    if not has_access(message.from_user.id):
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")
        return

    data = load_data()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if data.get('schedule_photo'):
        markup.add('🖼️ Просмотр расписания как фото')
    markup.add('🔙 Назад')
    bot.send_message(message.chat.id, "Выберите формат просмотра расписания:", reply_markup=markup)

# Просмотр расписания как фото
@bot.message_handler(regexp="🖼️ Просмотр расписания как фото")
def view_schedule_photo(message):
    if not has_access(message.from_user.id):
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")
        return

    data = load_data()
    if data.get('schedule_photo'):
        bot.send_photo(message.chat.id, open(data['schedule_photo'], 'rb'))
    else:
        bot.send_message(message.chat.id, "Фото расписания отсутствует.")

# Мероприятия: добавление мероприятия
@bot.message_handler(regexp="🎉 Мероприятия")
def events(message):
    if not has_access(message.from_user.id):
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")
        return

    if is_moderator(message.from_user.id):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('➕ Добавить мероприятие')
        markup.add('🔙 Назад')
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

@bot.message_handler(regexp="➕ Добавить мероприятие")
def add_event(message):
    if not has_access(message.from_user.id):
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")
        return

    if is_moderator(message.from_user.id):
        msg = bot.send_message(message.chat.id, "Введите дату мероприятия (в формате ГГГГ-ММ-ДД):")
        bot.register_next_step_handler(msg, process_event_date)

def process_event_date(message):
    date = message.text
    try:
        datetime.datetime.strptime(date, "%Y-%m-%d")
        msg = bot.send_message(message.chat.id, "Введите время мероприятия (в формате ЧЧ:ММ):")
        bot.register_next_step_handler(msg, process_event_time, date)
    except ValueError:
        bot.send_message(message.chat.id, "Некорректный формат даты. Пожалуйста, введите дату в формате ГГГГ-ММ-ДД.")

def process_event_time(message, date):
    time = message.text
    try:
        datetime.datetime.strptime(time, "%H:%M")
        msg = bot.send_message(message.chat.id, "Введите описание мероприятия:")
        bot.register_next_step_handler(msg, process_event_description, date, time)
    except ValueError:
        bot.send_message(message.chat.id, "Некорректный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ.")

def process_event_description(message, date, time):
    description = message.text
    data = load_data()
    data['events'].append({"date": date, "time": time, "description": description})
    save_data(data)
    bot.send_message(message.chat.id, "Мероприятие успешно добавлено.")

# Добавление расписания в виде фото
@bot.message_handler(regexp="📸 Добавить расписание как фото")
def add_schedule_photo(message):
    if not is_moderator(message.from_user.id):
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")
        return

    if load_data().get('schedule_photo'):
        bot.send_message(message.chat.id, "Расписание уже добавлено. Сначала удалите текущее расписание.")
        return

    msg = bot.send_message(message.chat.id, "Отправьте фото расписания:")
    bot.register_next_step_handler(msg, process_schedule_photo)

def process_schedule_photo(message):
    if message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        file_path = file_info.file_path
        file = bot.download_file(file_path)
        with open(os.path.join(SCHEDULE_PHOTO_PATH, 'schedule.jpg'), 'wb') as f:
            f.write(file)
        data = load_data()
        data['schedule_photo'] = os.path.join(SCHEDULE_PHOTO_PATH, 'schedule.jpg')
        save_data(data)
        bot.send_message(message.chat.id, "Фото расписания успешно добавлено.")
    else:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте фото.")

# Админка
@bot.message_handler(regexp="👑 Админка")
def admin_panel(message):
    if not has_access(message.from_user.id):
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")
        return

    if is_moderator(message.from_user.id):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('📸 Добавить расписание как фото', '🗑️ Удалить расписание', '📸 Добавить именинников', '🗑️ Удалить именинников', '➕ Добавить администратора', '🗑️ Удалить администратора')
        markup.add('🔙 Назад')
        bot.send_message(message.chat.id, "Админ панель:", reply_markup=markup)

# Удаление расписания: фото
@bot.message_handler(regexp="🗑️ Удалить расписание")
def delete_schedule_photo(message):
    if not is_moderator(message.from_user.id):
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")
        return

    data = load_data()
    if data.get('schedule_photo'):
        os.remove(data['schedule_photo'])
        data['schedule_photo'] = None
        save_data(data)
        bot.send_message(message.chat.id, "Расписание успешно удалено.")
    else:
        bot.send_message(message.chat.id, "Фото расписания отсутствует.")

# Добавление именинников
@bot.message_handler(regexp="📸 Добавить именинников")
def add_birthdays(message):
    if not is_moderator(message.from_user.id):
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")
        return

    msg = bot.send_message(message.chat.id, "Отправьте изображение именинников:")
    bot.register_next_step_handler(msg, process_birthdays_image)

def process_birthdays_image(message):
    if message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        file_path = file_info.file_path
        file = bot.download_file(file_path)
        month = datetime.datetime.now().strftime("%B").lower()
        file_name = f'birthdays_{month}.jpg'
        with open(os.path.join(BIRTHDAYS_PATH, file_name), 'wb') as f:
            f.write(file)
        data = load_data()
        data['birthdays'][month] = os.path.join(BIRTHDAYS_PATH, file_name)
        save_data(data)
        bot.send_message(message.chat.id, "Изображение именинников успешно добавлено.")
    else:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте изображение.")

# Удаление именинников
@bot.message_handler(regexp="🗑️ Удалить именинников")
def delete_birthdays(message):
    if not is_moderator(message.from_user.id):
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")
        return

    data = load_data()
    month = datetime.datetime.now().strftime("%B").lower()
    if month in data['birthdays']:
        os.remove(data['birthdays'][month])
        del data['birthdays'][month]
        save_data(data)
        bot.send_message(message.chat.id, "Изображение именинников успешно удалено.")
    else:
        bot.send_message(message.chat.id, "Изображение именинников отсутствует.")

# Добавление администратора
@bot.message_handler(regexp="➕ Добавить администратора")
def add_administrator(message):
    if not is_moderator(message.from_user.id):
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")
        return

    msg = bot.send_message(message.chat.id, "Введите ID пользователя для добавления в администраторы:")
    bot.register_next_step_handler(msg, process_add_administrator)

def process_add_administrator(message):
    user_id = int(message.text)
    moderators = load_moderators()
    if user_id not in moderators:
        moderators.append(user_id)
        save_moderators(moderators)
        bot.send_message(message.chat.id, f"Пользователь с ID {user_id} добавлен в администраторы.")
    else:
        bot.send_message(message.chat.id, "Этот пользователь уже является администратором.")

# Удаление администратора
@bot.message_handler(regexp="🗑️ Удалить администратора")
def remove_administrator(message):
    if not is_moderator(message.from_user.id):
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")
        return

    msg = bot.send_message(message.chat.id, "Введите ID пользователя для удаления из администраторов:")
    bot.register_next_step_handler(msg, process_remove_administrator)

def process_remove_administrator(message):
    user_id = int(message.text)
    moderators = load_moderators()
    if user_id in moderators:
        if user_id == ADMIN_ID:
            bot.send_message(message.chat.id, "Вы не можете удалить главного администратора.")
            return
        moderators.remove(user_id)
        save_moderators(moderators)
        bot.send_message(message.chat.id, f"Пользователь с ID {user_id} удален из администраторов.")
    else:
        bot.send_message(message.chat.id, "Этот пользователь не является администратором.")

# Функция для кнопки "Назад"
@bot.message_handler(regexp="🔙 Назад")
def back(message):
    start(message)

bot.polling()
