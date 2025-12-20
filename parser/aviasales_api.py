import os
import aiohttp

API_TOKEN = os.getenv("API_TOKEN")

async def fetch_json(url, params):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise RuntimeError(f"Ошибка API: {response.status}")

async def parse_flights(origin: str, destination: str, depart_date: str = None,
                        month: str = None, currency: str = "RUB", endpoint: str = "latest"):
    """
    Общий парсер рейсов.
    - origin, destination — города
    - depart_date — для latest
    - month — для calendar
    - currency — валюта
    - endpoint — "latest" или "calendar"
    """
    base_url = f"https://api.travelpayouts.com/v2/prices/{endpoint}"
    params = {"origin": origin, "destination": destination, "currency": currency, "token": API_TOKEN}
    if endpoint == "latest" and depart_date:
        params["depart_date"] = depart_date
    if endpoint == "calendar" and month:
        params["month"] = month
    return await fetch_json(base_url, params)
