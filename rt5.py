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

# Загрузка данных
def load_data():
    if not os.path.exists(DATA_FILE):
        return {'schedule': {}, 'access_list': []}
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

def reset_schedule():
    data = load_data()
    data['schedule'] = {}
    save_data(data)
    print("Расписание сброшено.")

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
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']
    for day in days:
        markup.add(day)
    markup.add('🔙 Назад')
    bot.send_message(message.chat.id, "Выберите день недели для просмотра расписания:", reply_markup=markup)

# Отображение расписания
@bot.message_handler(func=lambda message: message.text in ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница'])
def show_schedule(message):
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

# Админка
@bot.message_handler(regexp="👑 Админка")
def admin_panel(message):
    if is_moderator(message.from_user.id):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('➕ Добавить доступ', '➖ Убрать доступ', '📅 Добавить расписание', '🔄 Сбросить расписание', '📝 Изменить расписание', '🔙 Назад')
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
    else:
        bot.send_message(message.chat.id, "Пользователь не найден в списке доступов.")

# Добавление расписания: выбор дня
@bot.message_handler(regexp="📅 Добавить расписание")
def add_schedule(message):
    if is_moderator(message.from_user.id):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']
        for day in days:
            markup.add(day)
        markup.add('🔙 Назад')
        msg = bot.send_message(message.chat.id, "Выберите день недели для добавления расписания:", reply_markup=markup)
        bot.register_next_step_handler(msg, process_add_schedule_day)

def process_add_schedule_day(message):
    day = message.text
    msg = bot.send_message(message.chat.id, "Введите количество уроков для этого дня:")
    bot.register_next_step_handler(msg, process_add_schedule_lessons, day)

def process_add_schedule_lessons(message, day):
    try:
        lesson_count = int(message.text)
        data = load_data()
        data['schedule'][day] = []
        for i in range(lesson_count):
            msg = bot.send_message(message.chat.id, f"Введите название {i+1}-го урока:")
            bot.register_next_step_handler(msg, process_add_lesson_name, day, i, lesson_count, data)
    except ValueError:
        bot.send_message(message.chat.id, "Введите число.")

def process_add_lesson_name(message, day, i, lesson_count, data):
    lesson_name = message.text
    msg = bot.send_message(message.chat.id, f"Введите ФИО преподавателя для {lesson_name}:")
    bot.register_next_step_handler(msg, process_add_lesson_teacher, day, i, lesson_name, lesson_count, data)

def process_add_lesson_teacher(message, day, i, lesson_name, lesson_count, data):
    teacher_name = message.text
    data['schedule'][day].append({"lesson": lesson_name, "teacher": teacher_name})
    if i+1 == lesson_count:
        save_data(data)
        bot.send_message(message.chat.id, f"Расписание на {day} успешно добавлено.")
    else:
        msg = bot.send_message(message.chat.id, f"Введите название {i+2}-го урока:")
        bot.register_next_step_handler(msg, process_add_lesson_name, day, i+1, lesson_count, data)

# Сброс расписания
@bot.message_handler(regexp="🔄 Сбросить расписание")
def reset_schedule_command(message):
    if is_moderator(message.from_user.id):
        reset_schedule()
        bot.send_message(message.chat.id, "Расписание успешно сброшено.")

# Изменение расписания
@bot.message_handler(regexp="📝 Изменить расписание")
def edit_schedule(message):
    if is_moderator(message.from_user.id):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']
        for day in days:
            markup.add(day)
        markup.add('🔙 Назад')
        msg = bot.send_message(message.chat.id, "Выберите день недели для изменения расписания:", reply_markup=markup)
        bot.register_next_step_handler(msg, process_edit_schedule_day)

def process_edit_schedule_day(message):
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
