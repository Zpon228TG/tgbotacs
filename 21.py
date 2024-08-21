import requests
import random
import time
import datetime
import threading
from queue import Queue
from telegram import Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram.ext import MessageHandler, Filters
from telegram import Update

# Константы
API_URL = "https://botsapi.socpanel.com"
API_TOKEN = "wAiWKslGBzQI7Pop9xrJtb8iIN1tAU"
SERVICE_ID = "208621_1"
TELEGRAM_TOKEN = "6970413717:AAH190kZio-JIXyeSnZdlxHQzcczvSy0nsk"
TELEGRAM_CHAT_ID = "6578018656"

# Очередь заданий
order_queue = Queue()

# Счетчик выполненных заданий
completed_orders = 0
orders_lock = threading.Lock()

def getTimeStr():
    now = datetime.datetime.now()
    return f'[{now.hour}:{now.minute}:{now.second}]'

def randomInt():
    return random.randint(1, 1000000000000000000)

def getOrder():
    accId = randomInt()
    params = {
        "service_id": SERVICE_ID,
        "account_identity": accId,
        "api_token": API_TOKEN
    }
    try:
        response = requests.get(f"{API_URL}/getOrder", params=params)
        response.raise_for_status()  # Проверка на HTTP ошибки
        orderId = response.json().get('id')
        if orderId:
            return {'orderId': orderId, 'accId': accId}
        else:
            return {'error': 'Не удалось получить id заказа.'}
    except requests.RequestException as e:
        return {'error': str(e)}

def checkOrder(orderId, accId):
    params = {
        "order_id": orderId,
        "account_identity": accId,
        "api_token": API_TOKEN
    }
    try:
        response = requests.get(f"{API_URL}/check", params=params)
        response.raise_for_status()  # Проверка на HTTP ошибки
        return response.json()
    except requests.RequestException as e:
        return {'error': str(e)}

def process_orders():
    global completed_orders
    while True:
        order = order_queue.get()
        if order and 'orderId' in order:
            check_result = checkOrder(order['orderId'], order['accId'])
            with orders_lock:
                completed_orders += 1
                if completed_orders % 500 == 0:
                    send_telegram_message(f"Успешно выполнено {completed_orders} заданий!")
        order_queue.task_done()

def order_fetcher():
    while True:
        order = getOrder()
        if 'orderId' in order:
            order_queue.put(order)
        else:
            print(f"Ошибка при получении заказа: {order.get('error')}")
        time.sleep(1)  # задержка между запросами

def send_telegram_message(message):
    bot = Bot(token=TELEGRAM_TOKEN)
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

def start(update: Update, context: CallbackContext) -> None:
    context.bot.send_message(chat_id=update.effective_chat.id, text='Бот начал выполнение заказов!')

def main():
    # Настройка телеграм-бота
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))

    # Создание потоков для выполнения заказов
    for _ in range(5):  # количество потоков для выполнения заказов
        worker = threading.Thread(target=process_orders, daemon=True)
        worker.start()

    # Поток для получения заказов
    fetcher = threading.Thread(target=order_fetcher, daemon=True)
    fetcher.start()

    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
