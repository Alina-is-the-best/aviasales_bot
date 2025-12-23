import requests
import json

# Локальный справочник для мгновенного ответа (самые популярные)
PRIMARY_CITY_CODES = {
    "москва": "MOW",
    "санкт-петербург": "LED",
    "сочи": "AER",
}

def get_city_code(city_name: str) -> str:
    """
    Получает IATA код города. 
    Сначала ищет в локальном словаре, затем через Travelpayouts API.
    """
    city_name = city_name.lower().strip()
    
    # 1. Проверяем локальный список (быстрый доступ)
    if city_name in PRIMARY_CITY_CODES:
        return PRIMARY_CITY_CODES[city_name]

    # 2. Валидация символов
    invalid_sym = r'~!@#$%^&*()_+={}[]\|:;"<>,.?/0123456789'
    if any(char in invalid_sym for char in city_name):
        return None

    # 3. Запрос к API автодополнения
    try:
        url = f'https://autocomplete.travelpayouts.com/places2?locale=ru&types[]=city&term={city_name}'
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                # Берем код первого подходящего места
                return data[0].get('code')
    except Exception as e:
        print(f"Ошибка при поиске кода города: {e}")
    
    return None

def get_city_name_by_code(code: str) -> str:
    """Обратный поиск названия по коду (опционально)"""
    for name, c in PRIMARY_CITY_CODES.items():
        if c == code:
            return name.capitalize()
    return code