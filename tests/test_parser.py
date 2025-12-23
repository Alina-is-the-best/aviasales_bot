import sys
import os

# Добавляем родительскую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from api.aviasales_api import parse_flights
    print("✅ Модуль api успешно импортирован")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print(f"Текущий путь Python: {sys.path}")
    exit(1)

import asyncio

async def test():
    print("🔍 Тестируем API Aviasales...")
    
    result = await parse_flights(
        origin="MOW",  # Москва
        destination="AER",  # Сочи
        depart_date="2025-12-27",
        endpoint="latest"
    )
    
    print("\n📊 Результат API:")
    print(f"Тип ответа: {type(result)}")
    
    if isinstance(result, dict):
        print(f"Ключи в ответе: {list(result.keys())}")
        
        if 'success' in result:
            print(f"Успех: {result['success']}")
        
        if 'error' in result:
            print(f"Ошибка: {result['error']}")
        
        if 'data' in result:
            data = result['data']
            if isinstance(data, dict):
                print(f"Ключи в data: {list(data.keys())}")
                if len(data) > 0:
                    print(f"Первый ключ в data: {list(data.keys())[0]}")
                    first_item = data[list(data.keys())[0]]
                    print(f"Пример данных: {first_item}")
            else:
                print(f"Data не является словарем, тип: {type(data)}")
    else:
        print(f"Ответ не является словарем: {result}")

if __name__ == "__main__":
    print("🚀 Запуск теста...")
    asyncio.run(test())