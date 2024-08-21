import requests
import random
import time
import datetime

# Константы
API_URL = "https://botsapi.socpanel.com"
API_TOKEN = "wAiWKslGBzQI7Pop9xrJtb8iIN1tAU"
SERVICE_ID = "208621_1"
TELEGRAM_TOKEN = "6970413717:AAH190kZio-JIXyeSnZdlxHQzcczvSy0nsk"
ADMIN_ID = "6578018656"


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
    response = requests.get(f"{API_URL}/getOrder", params=params)
    if response.ok:
        orderId = response.json()['id']
        print(f'{getTimeStr()} Взял заказ {orderId}, ид акка {accId}')
        return {'orderId': orderId, 'accId': accId}
    else:
        print(f'{getTimeStr()} Кривой ответ, {response}')
        return {'error': f'Кривой ответ, {response}'}

def checkOrder(orderId, accId):
    params = {
        "order_id": orderId,
        "account_identity": accId,
        "api_token": API_TOKEN
    }
    response = requests.get(f"{API_URL}/check", params=params)
    return response.json()

def sendTelegramMessage(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": text
    }
    response = requests.post(url, params=params)
    if not response.ok:
        print(f'{getTimeStr()} Не удалось отправить сообщение в Telegram: {response}')

def main():
    execution_count = 0

    while True:
        getOrdersResponseObj = getOrder()
        if 'orderId' in getOrdersResponseObj:
            checkOrder(getOrdersResponseObj['orderId'], getOrdersResponseObj['accId'])
            execution_count += 1
            if execution_count % 500 == 0:
                sendTelegramMessage(ADMIN_ID, f'Выполнено {execution_count} операций.')
        time.sleep(1)  # Пауза между запросами, настройте по необходимости

if __name__ == "__main__":
    main()
