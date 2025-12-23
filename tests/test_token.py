# test_api_detailed.py
import asyncio
import aiohttp
from datetime import datetime

async def test():
    API_TOKEN = "12be481486d93ebad5ee84f0825002ad"  # из config.py
    
    print(f"Сегодня: {datetime.now().strftime('%d.%m.%Y')}")
    
    # Параметры как в боте
    params = {
        "token": API_TOKEN,
        "origin": "MOW",
        "destination": "AER",
        "depart_date": "2025-12-27",  # 27.12.2025 в правильном формате
        "currency": "RUB"
    }
    
    print(f"Параметры запроса: {params}")
    
    url = "https://api.travelpayouts.com/v1/prices/cheap"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            print(f"\nСтатус: {resp.status}")
            print(f"Заголовки: {dict(resp.headers)}")
            
            text = await resp.text()
            print(f"\nПолный ответ: {text}")
            
            # Пробуем другие endpoint
            print("\n--- Пробуем другие endpoint ---")
            
            # 1. Month matrix
            params2 = {
                "token": API_TOKEN,
                "origin": "MOW",
                "destination": "AER",
                "month": "2025-12",
                "currency": "RUB"
            }
            
            url2 = "https://api.travelpayouts.com/v2/prices/month-matrix"
            async with session.get(url2, params=params2) as resp2:
                print(f"\nMonth matrix статус: {resp2.status}")
                text2 = await resp2.text()
                print(f"Ответ: {text2[:500]}...")

asyncio.run(test())