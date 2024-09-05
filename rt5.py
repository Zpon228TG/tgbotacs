import telebot
import json
from datetime import datetime, timedelta

# Токен вашего бота
TOKEN = "7053322665:AAFe3nW8Ls3oThVaA1gDXCq7biaaolWe7IA"
bot = telebot.TeleBot(TOKEN)

# Основной администратор
MAIN_ADMIN_ID = 750334025  # Ваш Telegram ID

# Файлы для хранения данных
ALLOWED_USERS_FILE = "allowed_users.json"
MODERATORS_FILE = "moderators.json"
SCHEDULE_FILE = "schedule.json"
EVENTS_FILE = "events.json"

# Инициализация переменных
allowed_users = []
moderators = []
schedule = []
events = []

# Загрузка данных из JSON файлов
def load_json(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# Сохранение данных в JSON файлы
def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# Загрузка всех данных при запуске
allowed_users = load_json(ALLOWED_USERS_FILE)
moderators = load_json(MODERATORS_FILE)
schedule = load_json(SCHEDULE_FILE)
events = load_json(EVENTS_FILE)

# Меню
def main_menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎂 Именинники", "📚 Расписание")
    markup.add("🎉 Мероприятия", "👥 Список группы")
    if chat_id == MAIN_ADMIN_ID or chat_id in moderators:
        markup.add("➕ Добавить расписание", "➕ Добавить мероприятие")
    if chat_id == MAIN_ADMIN_ID:
        markup.add("➕ Добавить доступ", "➖ Убрать доступ", "➕ Добавить администратора")
    bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

# Функция для сброса расписания каждую субботу
def create_new_week_schedule():
    global schedule
    today = datetime.now()
    
    # Определение субботы текущей недели
    week_start = today - timedelta(days=today.weekday())
    saturday = week_start + timedelta(days=5)  # Суббота
    
    # Проверка, если сегодня суббота и расписание не сброшено
    if today > saturday and schedule:
        schedule = []
        save_json(SCHEDULE_FILE, schedule)
        print("Старое расписание очищено. Можно добавить новое расписание на следующую неделю.")

# Функция для отправки изображения именинников текущего месяца
@bot.message_handler(func=lambda message: message.text == "🎂 Именинники")
def send_birthday_image(message):
    if message.chat.id in allowed_users:
        # Получаем текущий месяц
        current_month = datetime.now().strftime("%B").lower()  # 'january', 'february', и т.д.
        
        # Путь к изображению именинников текущего месяца
        image_path = f"images/{current_month}.jpg"
        
        try:
            with open(image_path, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=f"🎉 Именинники в {current_month.capitalize()}")
        except FileNotFoundError:
            bot.send_message(message.chat.id, f"Изображение для именинников в {current_month.capitalize()} не найдено 🚫")
    else:
        bot.send_message(message.chat.id, "У вас нет прав для просмотра именинников 🚫")

# Функция для добавления пользователя
@bot.message_handler(func=lambda message: message.text == "➕ Добавить доступ")
def add_user(message):
    if message.chat.id == MAIN_ADMIN_ID or message.chat.id in moderators:
        msg = bot.send_message(message.chat.id, "Введите ID пользователя для добавления:")
        bot.register_next_step_handler(msg, process_add_user)
    else:
        bot.send_message(message.chat.id, "У вас нет прав для добавления пользователей 🚫")

def process_add_user(message):
    try:
        user_id = int(message.text)
        if user_id in allowed_users:
            bot.send_message(message.chat.id, "Пользователь уже имеет доступ ✅")
        else:
            allowed_users.append(user_id)
            save_json(ALLOWED_USERS_FILE, allowed_users)
            bot.send_message(message.chat.id, "Доступ пользователю добавлен ✅")
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат ID 🚫")

# Функция для удаления пользователя
@bot.message_handler(func=lambda message: message.text == "➖ Убрать доступ")
def remove_user(message):
    if message.chat.id == MAIN_ADMIN_ID or message.chat.id in moderators:
        msg = bot.send_message(message.chat.id, "Введите ID пользователя для удаления:")
        bot.register_next_step_handler(msg, process_remove_user)
    else:
        bot.send_message(message.chat.id, "У вас нет прав для удаления пользователей 🚫")

def process_remove_user(message):
    try:
        user_id = int(message.text)
        if user_id in allowed_users:
            allowed_users.remove(user_id)
            save_json(ALLOWED_USERS_FILE, allowed_users)
            bot.send_message(message.chat.id, "Доступ пользователю удален ❌")
        else:
            bot.send_message(message.chat.id, "Пользователь не найден в списке 🚫")
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат ID 🚫")

# Добавление администратора
@bot.message_handler(func=lambda message: message.text == "➕ Добавить администратора")
def add_moderator(message):
    if message.chat.id == MAIN_ADMIN_ID:
        msg = bot.send_message(message.chat.id, "Введите ID нового администратора:")
        bot.register_next_step_handler(msg, process_add_moderator)
    else:
        bot.send_message(message.chat.id, "У вас нет прав для добавления администраторов 🚫")

def process_add_moderator(message):
    try:
        user_id = int(message.text)
        if user_id in moderators:
            bot.send_message(message.chat.id, "Пользователь уже является администратором ✅")
        else:
            moderators.append(user_id)
            save_json(MODERATORS_FILE, moderators)
            bot.send_message(message.chat.id, "Администратор добавлен ✅")
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат ID 🚫")

# Функция просмотра расписания
@bot.message_handler(func=lambda message: message.text == "📚 Расписание")
def view_schedule(message):
    if message.chat.id in allowed_users:
        create_new_week_schedule()  # Проверяем и сбрасываем расписание по субботам
        if schedule:
            schedule_list = "\n".join([f"{item['lesson']}: {item['teacher']}" for item in schedule])
            bot.send_message(message.chat.id, f"Расписание на неделю:\n{schedule_list}")
        else:
            bot.send_message(message.chat.id, "Расписание на эту неделю еще не добавлено 🚫")
    else:
        bot.send_message(message.chat.id, "У вас нет прав для просмотра расписания 🚫")

# Добавление расписания (доступно только модераторам)
@bot.message_handler(func=lambda message: message.text == "➕ Добавить расписание")
def add_schedule(message):
    if message.chat.id in moderators or message.chat.id == MAIN_ADMIN_ID:
        msg = bot.send_message(message.chat.id, "Сколько уроков будет в расписании?")
        bot.register_next_step_handler(msg, process_schedule_count)
    else:
        bot.send_message(message.chat.id, "У вас нет прав модератора 🚫")

def process_schedule_count(message):
    try:
        lesson_count = int(message.text)
        bot.send_message(message.chat.id, f"Введите информацию для {lesson_count} уроков.")
        schedule.clear()  # Очищаем расписание перед добавлением нового
        save_json(SCHEDULE_FILE, schedule)
        for i in range(lesson_count):
            msg = bot.send_message(message.chat.id, f"Введите название урока {i + 1}:")
            bot.register_next_step_handler(msg, process_schedule_lesson, i)
    except ValueError:
        bot.send_message(message.chat.id, "Введите корректное количество уроков 🚫")

def process_schedule_lesson(message, index):
    lesson = message.text
    msg = bot.send_message(message.chat.id, f"Введите ФИО преподавателя для урока {lesson}:")
    bot.register_next_step_handler(msg, process_schedule_teacher, index, lesson)

def process_schedule_teacher(message, index, lesson):
    teacher = message.text
    schedule.append({'lesson': lesson, 'teacher': teacher})
    save_json(SCHEDULE_FILE, schedule)
    if index == len(schedule) - 1:
        bot.send_message(message.chat.id, "Расписание добавлено ✅")

# Запуск бота
bot.polling(none_stop=True)
