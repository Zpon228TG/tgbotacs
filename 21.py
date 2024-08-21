import requests
import random
import time
import datetime

# Константы
API_URL = "https://botsapi.socpanel.com"
API_TOKEN = "wAiWKslGBzQI7Pop9xrJtb8iIN1tAU"
SERVICE_ID = "208621_1"  

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
        print(f'Взял заказ {orderId}, ид акка {accId}')
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


while True:
    getOrdersResponseObj = getOrder()
    if 'orderId' in getOrdersResponseObj:
        print(checkOrder(getOrdersResponseObj['orderId'], getOrdersResponseObj['accId']))
