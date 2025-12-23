import sys
import os

# Добавляем родительскую директорию в путь Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from parser.aviasales_api import parse_flights
    from city_codes import get_city_code
    print("✅ Импорт из parser успешен")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Пути Python:", sys.path)
    sys.exit(1)

import asyncio

async def test():
    print("🔍 Тестирую API Москва → Сочи...")
    
    result = await parse_flights(
        origin=get_city_code("москва"),
        destination=get_city_code("сочи"),
        depart_date="2025-12-27",
        currency="RUB",
        endpoint="latest"
    )
    
    print("\n=== РЕЗУЛЬТАТ ===")
    if result.get("error"):
        print(f"❌ Ошибка: {result['error']}")
    else:
        data = result.get("data", {})
        print(f"✅ API ответ получен")
        print(f"Тип данных: {type(data)}")
        
        if isinstance(data, dict):
            print(f"Количество элементов: {len(data)}")
            
            if data:
                print("\nПервые 3 элемента:")
                for i, (key, value) in enumerate(list(data.items())[:3], 1):
                    print(f"\n{i}. Ключ: {key}")
                    print(f"   Тип значения: {type(value)}")
                    if isinstance(value, dict):
                        print(f"   Ключи в значении: {list(value.keys())}")
                        for k, v in list(value.items())[:5]:
                            print(f"   {k}: {v}")
        else:
            print(f"Данные: {data}")

if __name__ == "__main__":
    asyncio.run(test())