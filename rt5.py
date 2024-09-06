import telebot
from telebot import types
import json
import datetime
from apscheduler.schedulers.background import BackgroundScheduler

TOKEN = '7053322665:AAFe3nW8Ls3oThVaA1gDXCq7biaaolWe7IA'
ADMIN_ID = 750334025

bot = telebot.TeleBot(TOKEN)

# Файлы для хранения данных
ALLOWED_USERS_FILE = 'allowed_users.json'
BIRTHDAYS_FILE = 'birthdays.json'
SCHEDULE_FILE = 'schedule.json'
MODERATORS_FILE = 'moderators.json'

# Функция загрузки данных из JSON файла
def load_json(filename):
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Функция сохранения данных в JSON файл
def save_json(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file)

# Инициализация данных
allowed_users = load_json(ALLOWED_USERS_FILE)
moderators = load_json(MODERATORS_FILE)
birthdays = load_json(BIRTHDAYS_FILE)
schedule = load_json(SCHEDULE_FILE)

# Функция проверки доступа
def check_access(user_id):
    return str(user_id) in allowed_users or user_id == ADMIN_ID

# Главное меню
def main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if check_access(message.from_user.id):
        markup.add("Именинники", "Расписание", "Мероприятия")
        if message.from_user.id == ADMIN_ID or str(message.from_user.id) in moderators:
            markup.add("Добавить расписание", "Добавить именинника")
        if message.from_user.id == ADMIN_ID:
            markup.add("Добавить доступ", "Убрать доступ", "Добавить администратора")
    markup.add("Назад")
    bot.send_message(message.chat.id, "Главное меню", reply_markup=markup)

# Кнопка назад
def go_back_menu(message):
    main_menu(message)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_handler(message):
    main_menu(message)

# Добавить доступ
def add_access(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "Введите ID пользователя, которому вы хотите дать доступ:")
        bot.register_next_step_handler(msg, process_access)

def process_access(message):
    user_id = message.text
    if user_id in allowed_users:
        bot.send_message(message.chat.id, "Пользователь уже имеет доступ.")
    else:
        allowed_users[user_id] = True
        save_json(ALLOWED_USERS_FILE, allowed_users)
        bot.send_message(message.chat.id, "Доступ добавлен!")
    go_back_menu(message)

# Удалить доступ
def remove_access(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "Введите ID пользователя для удаления доступа:")
        bot.register_next_step_handler(msg, process_remove_access)

def process_remove_access(message):
    user_id = message.text
    if user_id in allowed_users:
        del allowed_users[user_id]
        save_json(ALLOWED_USERS_FILE, allowed_users)
        bot.send_message(message.chat.id, "Доступ удален!")
    else:
        bot.send_message(message.chat.id, "Такого пользователя нет в списке.")
    go_back_menu(message)

# Добавить администратора
def add_moderator(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "Введите ID пользователя, которого хотите сделать модератором:")
        bot.register_next_step_handler(msg, process_add_moderator)

def process_add_moderator(message):
    user_id = message.text
    if user_id in moderators:
        bot.send_message(message.chat.id, "Этот пользователь уже модератор.")
    else:
        moderators[user_id] = True
        save_json(MODERATORS_FILE, moderators)
        bot.send_message(message.chat.id, "Пользователь добавлен как модератор.")
    go_back_menu(message)

# Добавить расписание
def add_schedule(message):
    if message.from_user.id == ADMIN_ID or str(message.from_user.id) in moderators:
        msg = bot.send_message(message.chat.id, "Сколько уроков в расписании?")
        bot.register_next_step_handler(msg, process_schedule)

def process_schedule(message):
    lessons_count = int(message.text)
    schedule_data = {}
    for i in range(lessons_count):
        msg = bot.send_message(message.chat.id, f"Введите название урока {i+1}:")
        bot.register_next_step_handler(msg, lambda m, i=i: process_lesson_name(m, i, schedule_data, lessons_count))

def process_lesson_name(message, lesson_index, schedule_data, lessons_count):
    lesson_name = message.text
    msg = bot.send_message(message.chat.id, f"Введите ФИО преподавателя для урока {lesson_index+1}:")
    bot.register_next_step_handler(msg, lambda m, lesson_name=lesson_name, lesson_index=lesson_index, lessons_count=lessons_count: process_teacher_name(m, lesson_name, lesson_index, schedule_data, lessons_count))

def process_teacher_name(message, lesson_name, lesson_index, schedule_data, lessons_count):
    teacher_name = message.text
    schedule_data[f"lesson_{lesson_index+1}"] = {"name": lesson_name, "teacher": teacher_name}
    
    if len(schedule_data) == lessons_count:
        schedule[str(datetime.date.today())] = schedule_data
        save_json(SCHEDULE_FILE, schedule)
        bot.send_message(message.chat.id, "Расписание успешно добавлено!")
        go_back_menu(message)

# Показать расписание
def show_schedule(message):
    if not schedule:
        bot.send_message(message.chat.id, "Расписание не найдено.")
    else:
        schedule_str = ""
        for date, lessons in schedule.items():
            schedule_str += f"Дата: {date}\n"
            for lesson_num, lesson_info in lessons.items():
                schedule_str += f"{lesson_num}: {lesson_info['name']} - {lesson_info['teacher']}\n"
        bot.send_message(message.chat.id, schedule_str)

# Добавить именинника
def add_birthday(message):
    if message.from_user.id == ADMIN_ID or str(message.from_user.id) in moderators:
        msg = bot.send_message(message.chat.id, "Введите имя именинника:")
        bot.register_next_step_handler(msg, process_birthday_name)

def process_birthday_name(message):
    name = message.text
    msg = bot.send_message(message.chat.id, "Введите дату рождения (в формате ГГГГ-ММ-ДД):")
    bot.register_next_step_handler(msg, lambda m, name=name: process_birthday_date(m, name))

def process_birthday_date(message, name):
    birthday = message.text
    user_id = message.from_user.id
    birthdays[name] = {"birthday": birthday, "user_id": user_id}
    save_json(BIRTHDAYS_FILE, birthdays)
    bot.send_message(message.chat.id, "Именинник добавлен!")
    go_back_menu(message)

# Поздравить именинников
def check_birthdays():
    today = datetime.date.today()
    for name, info in birthdays.items():
        birthday = datetime.datetime.strptime(info['birthday'], "%Y-%m-%d").date()
        if (birthday - today).days == 1:
            bot.send_message(info['user_id'], f"Завтра день рождения у {name}!")
        elif birthday == today:
            bot.send_message(info['user_id'], f"С Днем Рождения, {name}!")

# Функция для проверки именинников каждые сутки
def schedule_birthday_check():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_birthdays, 'interval', days=1)
    scheduler.start()

# Запуск проверки именинников
schedule_birthday_check()

# Обработчик кнопок
@bot.message_handler(func=lambda message: True)
def button_handler(message):
    if message.text == "Именинники":
        check_birthdays()
    elif message.text == "Расписание":
        show_schedule(message)
    elif message.text == "Мероприятия":
        bot.send_message(message.chat.id, "Список мероприятий скоро будет доступен.")
    elif message.text == "Добавить расписание":
        add_schedule(message)
    elif message.text == "Добавить именинника":
        add_birthday(message)
    elif message.text == "Добавить доступ":
        add_access(message)
    elif message.text == "Убрать доступ":
        remove_access(message)
    elif message.text == "Добавить администратора":
        add_moderator(message)
    elif message.text == "Назад":
        go_back_menu(message)
    else:
        bot.send_message(message.chat.id, "Неизвестная команда.")

# Поллинг бота
bot.polling(none_stop=True)
