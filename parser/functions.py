from parser import parse_flights

async def get_latest_flights(origin: str, destination: str, depart_date: str, currency: str = "RUB"):
    '''Возвращает JSON с рейсами'''
    data = await parse_flights(origin, destination, depart_date=depart_date, currency=currency, endpoint="latest")
    return data

async def get_calendar_prices(origin: str, destination: str, month: str, currency: str = "RUB"):
    '''Возвращает JSON с календарными ценами'''
    data = await parse_flights(origin, destination, month=month, currency=currency, endpoint="calendar")
    return data

def filter_by_price(flights, max_price: float):
    '''Возвращает только те рейсы, цена которых ≤ max_price'''
    return [f for f in flights if f.get("price") <= max_price]

def filter_by_baggage(flights, baggage_included: bool):
    '''Отбирает рейсы по наличию включённого багажа'''
    return [f for f in flights if f.get("bags_included") == baggage_included]

def filter_by_stops(flights, max_stops: int):
    '''Отбирает рейсы по количеству пересадок'''
    return [f for f in flights if f.get("number_of_changes") <= max_stops]

def filter_by_airline(flights, allowed_airlines: list):
    '''Отбирает рейсы по списку разрешённых авиакомпаний'''
    return [f for f in flights if f.get("airline") in allowed_airlines]
