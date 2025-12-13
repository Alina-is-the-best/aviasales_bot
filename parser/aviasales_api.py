import os
import requests
import filters_repository as filters_repo


API_TOKEN = os.getenv("API_TOKEN")

def get_flight_price(origin: str, destination: str, depart_date: str, currency: str):
    url = "https://api.travelpayouts.com/v2/prices/latest"
    params = {
        "origin": origin,
        "destination": destination,
        "depart_date": depart_date,
        "currency": currency,
        "token": API_TOKEN
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        raise RuntimeError(f"Ошибка API: {response.status_code}")



def get_calendar_prices(origin: str, destination: str, month: str, currency: str):
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

async def get_user_currency(user_id: int) -> str:
    """
    Возвращает валюту пользователя из фильтров.
    """
    currency = await filters_repo.get_filter(user_id, "currency")
    if currency in ["RUB", "USD", "EUR"]:
        return currency
    return "RUB"