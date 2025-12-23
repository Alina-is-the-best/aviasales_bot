import asyncio
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
<<<<<<< Updated upstream:hot.py

import keyboards
from states import HotTickets

from parser.aviasales_api import parse_flights
from city_codes import get_city_code
from datetime import datetime
=======
from keyboards import keyboards
from states import HotTickets
from api.aviasales_api import parse_flights
from data.city_codes import get_city_code
from utils.utils import format_one_way_ticket, is_date_in_coming_week
>>>>>>> Stashed changes:handlers/hot.py

router = Router()

# Маленький словарик для красоты (SOLID: вынос данных)
CITY_NAMES_RU = {
    'LED': 'Санкт-Петербург',
    'AER': 'Сочи',
    'KZN': 'Казань',
    'MRV': 'Мин. Воды',
    'KGD': 'Калининград',
    'IST': 'Стамбул',
    'DXB': 'Дубай'
}

def register(dp):
    dp.include_router(router)

<<<<<<< Updated upstream:hot.py

# Первый шаг — выбираем город
=======
>>>>>>> Stashed changes:handlers/hot.py
@router.message(F.text == "Горячие билеты")
async def hot_start(msg: types.Message, state: FSMContext):
    await state.set_state(HotTickets.from_city)
    await msg.answer("🔥 Откуда летим?", reply_markup=keyboards.back_to_main())

@router.message(HotTickets.from_city)
async def hot_from_city(msg: types.Message, state: FSMContext):
    code = get_city_code(msg.text)
    if not code:
        return await msg.answer("❌ Город не найден. Попробуйте еще раз.")
    
    await state.update_data(from_city=msg.text, from_code=code)
    await state.set_state(HotTickets.to_city)
    await msg.answer(
        f"Куда летим?", 
        reply_markup=keyboards.hot_dest_kb()
    )

<<<<<<< Updated upstream:hot.py

# Второй шаг — ловим введённый город
@router.message(HotTickets.from_city)
# Обновите функцию hot_city_received:
async def hot_city_received(msg: types.Message, state: FSMContext):
    if msg.text == "⬅️ Назад в меню":
        await state.clear()
        return await msg.answer("Главное меню:", reply_markup=keyboards.main_menu())
    
    user_city = msg.text.strip()
    city_code = get_city_code(user_city)
    
    await msg.answer(f"Ищу горячие билеты из: {user_city} ({city_code}) 🔥")
    
    try:
        # Для горячих билетов ищем популярные направления
        # Покажем несколько примерных направлений
        popular_destinations = ['LED', 'AER', 'KRR', 'KZN', 'SVX']  # СПб, Сочи, Краснодар, Казань, Екатеринбург
=======
@router.message(HotTickets.to_city)
async def hot_finish(msg: types.Message, state: FSMContext):
    # 1. ОБРАБОТКА КНОПКИ НАЗАД
    if msg.text == "⬅️ Назад в меню":
        await state.clear()
        return await msg.answer("Вы вернулись в главное меню", reply_markup=keyboards.main_menu())

    data = await state.get_data()
    from_code = data.get('from_code')
    from_city_name = data.get('from_city')

    # 2. РЕЖИМ "КУДА УГОДНО"
    if msg.text == "🌍 Куда угодно":
        await msg.answer("🔎 Ищу лучшие варианты по разным направлениям...")
>>>>>>> Stashed changes:handlers/hot.py
        
        popular_dest = ['LED', 'AER', 'KZN', 'MRV', 'KGD', 'IST', 'DXB']
        
<<<<<<< Updated upstream:hot.py
        for dest_code in popular_destinations[:3]:  # Проверим первые 3
            result = await parse_flights(
                origin=city_code,
                destination=dest_code,
                depart_date="2025-12-27",  # Ближайшая дата
                currency="RUB",
                endpoint="latest"
            )
            
            if result.get("data"):
                for dest, flights_dict in result["data"].items():
                    if isinstance(flights_dict, dict):
                        for flight_key, flight in flights_dict.items():
                            if isinstance(flight, dict):
                                price = flight.get('price', '?')
                                airline = flight.get('airline', '?')
                                departure = flight.get('departure_at', '?').split('T')[0] if flight.get('departure_at') else '?'
                                
                                # Получаем название города по коду
                                dest_name = dest  # Можно добавить обратный словарь кодов
                                response_text += (
                                    f"• {user_city} → {dest_name}\n"
                                    f"  💰 От {price}₽\n"
                                    f"  🏢 {airline}\n"
                                    f"  📅 {departure}\n\n"
                                )
                                break  # Только первый билет
                        break
=======
        # Запускаем все запросы одновременно
        tasks = [parse_flights(from_code, d, endpoint="latest") for d in popular_dest]
        results = await asyncio.gather(*tasks)

        all_flights = []
        for res in results:
            flights_data = res.get('data', [])
            if isinstance(flights_data, list):
                # Фильтруем только на ближайшую неделю
                hot = [f for f in flights_data if is_date_in_coming_week(f.get('departure_at'))]
                all_flights.extend(hot)

        if not all_flights:
            return await msg.answer("😔 На ближайшую неделю билетов 'куда угодно' не нашлось.")

        # СОРТИРОВКА И УДАЛЕНИЕ ДУБЛИКАТОВ ГОРОДОВ
        all_flights.sort(key=lambda x: x.get('price', 999999))
>>>>>>> Stashed changes:handlers/hot.py
        
        unique_flights = []
        seen_cities = set()

        for f in all_flights:
            dest_code = f.get('destination')
            if dest_code not in seen_cities:
                unique_flights.append(f)
                seen_cities.add(dest_code)
            if len(unique_flights) == 3: # Нам нужно 3 разных города
                break
# Если нашли меньше 3 "горячих", добираем остальные просто по цене
        if len(unique_flights) < 3:
            for f in all_flights:
                dest_code = f.get('destination')
                if dest_code not in seen_cities:
                    unique_flights.append(f)
                    seen_cities.add(dest_code)
                if len(unique_flights) == 3:
                    break

        response = "🌍 **Топ выгодных направлений:**\n\n"
        # Если в списке меньше 3 даже после добора (бывает и такое)
        for i, f in enumerate(unique_flights, 1):
            dest_iata = f.get('destination')
            dest_name = CITY_NAMES_RU.get(dest_iata, dest_iata)
            response += format_one_way_ticket(f, from_city_name, dest_name, i)

        await msg.answer(response, parse_mode="Markdown", disable_web_page_preview=True)
        return await state.clear()

    # 3. ОБЫЧНЫЙ РЕЖИМ (ПОИСК В КОНКРЕТНЫЙ ГОРОД)
    dest_code = get_city_code(msg.text)
    if not dest_code:
        return await msg.answer("❌ Город не найден. Попробуйте другой или нажмите 'Куда угодно'.")

    await msg.answer(f"🔎 Ищу билеты в {msg.text} на ближайшую неделю...")
    
    result = await parse_flights(from_code, dest_code, endpoint="latest")
    flights = result.get('data', [])

    if not flights:
        return await msg.answer("😔 Билетов не найдено.")

    hot_now = [f for f in flights if is_date_in_coming_week(f.get('departure_at'))]

    if not hot_now:
        await msg.answer("⏳ На этой неделе билетов нет, вот самый выгодный на ближайшую дату:")
        best_flight = flights[0]
    else:
        best_flight = min(hot_now, key=lambda x: x.get('price', 999999))

    response = "🔥 **Самый горячий билет:**\n\n"
    response += format_one_way_ticket(best_flight, from_city_name, msg.text)

    await msg.answer(response, parse_mode="Markdown", disable_web_page_preview=True)
    await state.clear()