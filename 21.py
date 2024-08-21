import requests
import random
import time
import datetime
from telegram import Bot

# Константы
API_URL = "https://botsapi.socpanel.com"
API_TOKEN = "wAiWKslGBzQI7Pop9xrJtb8iIN1tAU"
SERVICE_ID = "208621_1"  
TELEGRAM_BOT_TOKEN = "6970413717:AAH190kZio-JIXyeSnZdlxHQzcczvSy0nsk"
CHAT_ID = "6578018656"

# Инициализация бота
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def getTimeStr():
    time = datetime.datetime.now()
    return f'[{time.hour}:{time.minute}:{time.second}]'

def randomInt():
    return random.randint(1, 1000000000000000000)

def getOrder():
    accId = randomInt()
    params = {
        "service_id": SERVICE_ID,
        "account_identity": accId,
        "api_token": API_TOKEN
    }
    response = requests.get(f"{API_URL}/getOrder", params=params)
    if response.ok:
        orderId = response.json()['id']
        return {'orderId': orderId, 'accId': accId}
    else:
        return {'error': f'Кривой ответ, {response}'}

def checkOrder(orderId, accId):
    params = {
        "order_id": orderId,
        "account_identity": accId,
        "api_token": API_TOKEN
    }
    response = requests.get(f"{API_URL}/check", params=params)
    return response.json()

order_count = 0
while True:
    getOrdersResponseObj = getOrder()
    if 'orderId' in getOrdersResponseObj:
        order_count += 1
        check_result = checkOrder(getOrdersResponseObj['orderId'], getOrdersResponseObj['accId'])
        
        # Отправка сообщения каждые 500 заказов
        if order_count % 500 == 0:
            bot.send_message(chat_id=CHAT_ID, text=f'Успешно обработано {order_count} заказов. {getTimeStr()}')

    # Добавляем небольшую задержку, чтобы избежать излишней нагрузки на сервер
    time.sleep(1)
