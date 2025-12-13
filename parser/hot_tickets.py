from datetime import datetime, timedelta
from .aviasales_api import get_flight_price, get_user_currency

async def get_hot_tickets(user_id: int, origin: str, destination: str, days_ahead: int = 7):
    """
    Находит самые дешёвые билеты на ближайшие N дней.
    Возвращает список словарей с ключами: date, price, airline, flight_number
    """
    hot_tickets = []
    currency = await get_user_currency(user_id)

    for i in range(days_ahead):
        date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
        try:
            data = get_flight_price(origin, destination, date, currency)
        except RuntimeError as e:
            print(f"Ошибка API для даты {date}: {e}")
            continue

        day_prices = data.get("data", {}).get(destination, {})
        for d, info in day_prices.items():
            hot_tickets.append({
                "date": d,
                "price": info.get("price"),
                "airline": info.get("airline"),
                "flight_number": info.get("flight_number")
            })

    hot_tickets.sort(key=lambda x: x["price"] if x["price"] else float("inf"))
    return hot_tickets[:5]
