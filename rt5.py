import telebot
from telebot import types
import json
import datetime
import pytz
import os

TOKEN = '7053322665:AAFe3nW8Ls3oThVaA1gDXCq7biaaolWe7IA'
ADMIN_ID = 750334025

bot = telebot.TeleBot(TOKEN)

# Файлы для хранения данных
DATA_FILE = 'data.json'
MODERATORS_FILE = 'moderators.json'
BIRTHDAYS_PATH = '.'  # Папка с изображениями именинников в той же директории
SCHEDULE_PHOTO_PATH = '.'  # Папка с изображениями расписания в той же директории

# Загрузка данных
def load_data():
    if not os.path.exists(DATA_FILE):
        return {'schedule': {}, 'access_list': [], 'events': [], 'schedule_photo': None}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

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

# Проверка доступа
def has_access(user_id):
    data = load_data()
    return user_id in data['access_list'] or user_id == ADMIN_ID

def is_moderator(user_id):
    moderators = load_moderators()
    return user_id in moderators

# Начальное меню
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('📅 Именинники', '📚 Расписание', '🎉 Мероприятия')
    if is_moderator(message.from_user.id):
        markup.add('👑 Админка')
    bot.send_message(message.chat.id, "Добро пожаловать!", reply_markup=markup)

# Отправка изображения с именинниками
@bot.message_handler(regexp="📅 Именинники")
def birthdays(message):
    month = datetime.datetime.now().strftime("%B").lower()
    file_path = os.path.join(BIRTHDAYS_PATH, f'{month}.jpg')
    if os.path.exists(file_path):
        bot.send_photo(message.chat.id, open(file_path, 'rb'))
    else:
        bot.send_message(message.chat.id, "Изображение именинников для этого месяца отсутствует.")
        print(f"Изображение для месяца {month} отсутствует.")

# Расписание: выбор дня недели
@bot.message_handler(regexp="📚 Расписание")
def schedule(message):
    data = load_data()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if data['schedule_photo']:
        markup.add('🖼️ Просмотр расписания как фото', '📄 Просмотр расписания как текст')
    else:
        markup.add('📄 Просмотр расписания как текст')
    markup.add('🔙 Назад')
    bot.send_message(message.chat.id, "Выберите формат просмотра расписания:", reply_markup=markup)

# Просмотр расписания как текст
@bot.message_handler(regexp="📄 Просмотр расписания как текст")
def view_schedule_text(message):
    data = load_data()
    if not data['schedule']:
        bot.send_message(message.chat.id, "Расписание отсутствует.")
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']
    for day in days:
        markup.add(day)
    markup.add('🔙 Назад')
    bot.send_message(message.chat.id, "Выберите день недели для просмотра расписания:", reply_markup=markup)

# Просмотр расписания как текст: отображение
@bot.message_handler(func=lambda message: message.text in ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница'])
def show_schedule_text(message):
    day = message.text
    data = load_data()
    schedule = data.get('schedule', {}).get(day, [])
    if schedule:
        response = f"Расписание на {day}:\n\n"
        for i, lesson in enumerate(schedule):
            response += f"{i+1}. {lesson['lesson']} - {lesson['teacher']}\n"
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, f"Расписание на {day} отсутствует.")

# Просмотр расписания как фото
@bot.message_handler(regexp="🖼️ Просмотр расписания как фото")
def view_schedule_photo(message):
    data = load_data()
    if data['schedule_photo']:
        bot.send_photo(message.chat.id, open(data['schedule_photo'], 'rb'))
    else:
        bot.send_message(message.chat.id, "Фото расписания отсутствует.")

# Мероприятия: добавление мероприятия
@bot.message_handler(regexp="🎉 Мероприятия")
def events(message):
    if is_moderator(message.from_user.id):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('➕ Добавить мероприятие', '🔙 Назад')
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

@bot.message_handler(regexp="➕ Добавить мероприятие")
def add_event(message):
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

# Админка
@bot.message_handler(regexp="👑 Админка")
def admin_panel(message):
    if is_moderator(message.from_user.id):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('➕ Добавить доступ', '➖ Убрать доступ', '📅 Добавить расписание', '🔄 Сбросить расписание', '📝 Изменить расписание', '🖼️ Добавить расписание как фото', '🗑️ Удалить расписание', '🔙 Назад')
        bot.send_message(message.chat.id, "Админ панель:", reply_markup=markup)

# Добавление доступа
@bot.message_handler(regexp="➕ Добавить доступ")
def add_access(message):
    if is_moderator(message.from_user.id):
        msg = bot.send_message(message.chat.id, "Введите ID пользователя для добавления доступа:")
        bot.register_next_step_handler(msg, process_add_access)

def process_add_access(message):
    user_id = int(message.text)
    data = load_data()
    if user_id in data['access_list']:
        bot.send_message(message.chat.id, "Этот пользователь уже имеет доступ.")
    else:
        data['access_list'].append(user_id)
        save_data(data)
        bot.send_message(message.chat.id, "Доступ успешно добавлен.")

# Удаление доступа
@bot.message_handler(regexp="➖ Убрать доступ")
def remove_access(message):
    if is_moderator(message.from_user.id):
        msg = bot.send_message(message.chat.id, "Введите ID пользователя для удаления доступа:")
        bot.register_next_step_handler(msg, process_remove_access)

def process_remove_access(message):
    user_id = int(message.text)
    data = load_data()
    if user_id in data['access_list']:
        data['access_list'].remove(user_id)
        save_data(data)
        bot.send_message(message.chat.id, "Доступ успешно удален.")
        if user_id == message.from_user.id:
            bot.send_message(message.chat.id, "Вы больше не имеете доступа к этому боту.")
    else:
        bot.send_message(message.chat.id, "Пользователь не найден в списке доступов.")

# Добавление расписания: фото
@bot.message_handler(regexp="🖼️ Добавить расписание как фото")
def add_schedule_photo(message):
    if is_moderator(message.from_user.id):
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

# Удаление расписания: фото
@bot.message_handler(regexp="🗑️ Удалить расписание")
def delete_schedule_photo(message):
    if is_moderator(message.from_user.id):
        data = load_data()
        if data.get('schedule_photo'):
            os.remove(data['schedule_photo'])
            data['schedule_photo'] = None
            save_data(data)
            bot.send_message(message.chat.id, "Расписание успешно удалено.")
        else:
            bot.send_message(message.chat.id, "Фото расписания отсутствует.")

# Изменение расписания
@bot.message_handler(regexp="📝 Изменить расписание")
def modify_schedule(message):
    if is_moderator(message.from_user.id):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']
        for day in days:
            markup.add(day)
        markup.add('🔙 Назад')
        bot.send_message(message.chat.id, "Выберите день недели для изменения расписания:", reply_markup=markup)
        bot.register_next_step_handler(message, process_modify_schedule_day)

def process_modify_schedule_day(message):
    day = message.text
    data = load_data()
    schedule = data.get('schedule', {}).get(day, [])
    if schedule:
        response = f"Расписание на {day}:\n\n"
        for i, lesson in enumerate(schedule):
            response += f"{i+1}. {lesson['lesson']} - {lesson['teacher']}\n"
        bot.send_message(message.chat.id, response)
        msg = bot.send_message(message.chat.id, "Введите номер урока, который хотите изменить:")
        bot.register_next_step_handler(msg, process_edit_lesson_number, day, schedule)
    else:
        bot.send_message(message.chat.id, f"Расписание на {day} отсутствует.")

def process_edit_lesson_number(message, day, schedule):
    try:
        lesson_number = int(message.text) - 1
        if 0 <= lesson_number < len(schedule):
            lesson = schedule[lesson_number]
            msg = bot.send_message(message.chat.id, f"Текущие данные:\nУрок: {lesson['lesson']}\nПреподаватель: {lesson['teacher']}\nВведите новое название урока:")
            bot.register_next_step_handler(msg, process_edit_lesson_name, day, lesson_number, schedule)
        else:
            bot.send_message(message.chat.id, "Номер урока вне диапазона.")
    except ValueError:
        bot.send_message(message.chat.id, "Введите номер урока.")

def process_edit_lesson_name(message, day, lesson_number, schedule):
    new_lesson_name = message.text
    msg = bot.send_message(message.chat.id, "Введите новое имя преподавателя:")
    bot.register_next_step_handler(msg, process_edit_lesson_teacher, day, lesson_number, new_lesson_name, schedule)

def process_edit_lesson_teacher(message, day, lesson_number, new_lesson_name, schedule):
    new_teacher_name = message.text
    schedule[lesson_number] = {"lesson": new_lesson_name, "teacher": new_teacher_name}
    data = load_data()
    data['schedule'][day] = schedule
    save_data(data)
    bot.send_message(message.chat.id, f"Расписание на {day} обновлено.")

# Сброс расписания
@bot.message_handler(regexp="🔄 Сбросить расписание")
def reset_schedule(message):
    if is_moderator(message.from_user.id):
        data = load_data()
        if data.get('schedule_photo'):
            os.remove(data['schedule_photo'])
            data['schedule_photo'] = None
        data['schedule'] = {}
        save_data(data)
        bot.send_message(message.chat.id, "Расписание успешно сброшено.")

# Кнопка "Назад"
@bot.message_handler(regexp="🔙 Назад")
def go_back(message):
    start(message)

# Обработка всех остальных сообщений
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.text.lower() == 'погода':
        bot.send_message(message.chat.id, "Погода сегодня отличная!")
    else:
        bot.send_message(message.chat.id, "Неизвестная команда.")

bot.polling(none_stop=True)
