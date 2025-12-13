import os
import requests

API_TOKEN = os.getenv("API_TOKEN")

def get_flight_price(origin, destination, depart_date):
    url = "https://api.travelpayouts.com/v2/prices/latest"
    params = {
        "origin": origin,
        "destination": destination,
        "depart_date": depart_date,
        "token": API_TOKEN
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()  # JSON с ценами
    else:
        raise RuntimeError(f"Ошибка API: {response.status_code}")


def get_calendar_prices(origin, destination, month):
    url = "https://api.travelpayouts.com/v2/prices/calendar"
    params = {
        "origin": origin,
        "destination": destination,
        "month": month,  #YYYY-MM
        "token": API_TOKEN
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()  # JSON с ценами по дням
    else:
        raise RuntimeError(f"Ошибка API: {response.status_code}")
