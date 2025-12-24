from .client import fetch_json
from infra.config import API_TOKEN
import logging

async def parse_flights(origin: str, destination: str, depart_date: str = None,
                        return_date: str = None, month: str = None, currency: str = "RUB", endpoint: str = "latest"):
    """
    Общий парсер рейсов.
    """
    print(f"=== API CALL ===")
    print(f"Origin: {origin}, Destination: {destination}")
    print(f"Depart date: {depart_date}, Return date: {return_date}, Endpoint: {endpoint}")
    
    if endpoint == "latest":
        base_url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
        params = {
            "token": API_TOKEN,
            "origin": origin.upper(),
            "destination": destination.upper(),
            "currency": currency,
            "sorting": "price",
            "limit": 30,
            "one_way": "true",
            "market": "ru",
            "locale": "ru",
        }
        # Добавляем дату ТОЛЬКО если она передана (не None)
        if depart_date:
            params["departure_at"] = depart_date

    elif endpoint == "calendar":
        base_url = "https://api.travelpayouts.com/v2/prices/month-matrix"
        params = {
            "token": API_TOKEN,
            "origin": origin.upper(),
            "destination": destination.upper(),
            "month": month,
            "currency": currency,
        }
    elif endpoint == "dates":
        base_url = "https://api.travelpayouts.com/v2/prices/week-matrix"
        params = {
            "token": API_TOKEN,
            "origin": origin.upper(),
            "destination": destination.upper(),
            "depart_date": depart_date,
            "return_date": return_date,
            "currency": currency,
        }
    else:
        return {"error": f"Unknown endpoint: {endpoint}", "data": {}}
    
    print(f"URL: {base_url}")
    print(f"Params: {params}")
    
    try:
        result = await fetch_json(base_url, params)
        print(f"API Response received, type: {type(result)}")
        
        # ОТЛАДКА: выводим структуру ответа
        print(f"=== API RESPONSE STRUCTURE ===")
        if isinstance(result, dict):
            print(f"Result keys: {list(result.keys())}")
            if 'data' in result:
                data = result['data']
                print(f"'data' type: {type(data)}")
                if isinstance(data, list) and data:
                    print(f"First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")
        print(f"=== END STRUCTURE ===")
        
        return result

    except Exception as e:
        logging.error(f"API Error: {e}")
        return {"error": str(e), "data": []}