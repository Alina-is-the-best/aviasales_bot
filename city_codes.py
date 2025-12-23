"""
Справочник кодов городов для Aviasales API
"""

CITY_CODES = {
    # Россия
    "москва": "MOW",
    "москвы": "MOW",
    "мск": "MOW",
    "сочи": "AER",
    "сочи": "AER",
    "санкт-петербург": "LED",
    "питер": "LED",
    "спб": "LED",
    "казань": "KZN",
    "екатеринбург": "SVX",
    "новосибирск": "OVB",
    "краснодар": "KRR",
    "минск": "MSQ",
    "киев": "KBP",
    "астана": "NQZ",
    "алматы": "ALA",
    
    # Международные
    "лондон": "LON",
    "париж": "PAR",
    "берлин": "BER",
    "нью-йорк": "NYC",
    "дубай": "DXB",
    "стамбул": "IST",
}

def get_city_code(city_name: str) -> str:
    """Преобразует название города в IATA код"""
    city_lower = city_name.lower().strip()
    
    # Прямое совпадение
    if city_lower in CITY_CODES:
        return CITY_CODES[city_lower]
    
    # Проверяем частичные совпадения
    for key, code in CITY_CODES.items():
        if key in city_lower or city_lower in key:
            return code
    
    # Если не нашли - возвращаем как есть (может быть уже кодом)
    return city_name.upper()