import asyncio
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from infra.keyboards import keyboards
from infra.states import HotTickets
from adapters.api.aviasales_api import parse_flights
from models.data.city_codes import get_city_code
from utils.utils import format_one_way_ticket, is_date_in_coming_week

router = Router()

# Маленький словарик для красоты названий городов
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

# 1. Начало диалога — кнопка из главного меню
@router.message(F.text == "Горячие билеты")
async def hot_start(msg: types.Message, state: FSMContext):
    await state.set_state(HotTickets.from_city)
    await msg.answer("🔥 Откуда летим?", reply_markup=keyboards.back_to_main())

# 2. Получаем город вылета
@router.message(HotTickets.from_city)
async def hot_from_city(msg: types.Message, state: FSMContext):
    if msg.text == "⬅️ Назад в меню":
        await state.clear()
        return await msg.answer("Главное меню:", reply_markup=keyboards.main_menu())

    code = get_city_code(msg.text)
    if not code:
        return await msg.answer("❌ Город не найден. Попробуйте еще раз.")
    
    await state.update_data(from_city=msg.text, from_code=code)
    await state.set_state(HotTickets.to_city)
    await msg.answer(
        f"Куда летим из {msg.text}?", 
        reply_markup=keyboards.hot_dest_kb()
    )

# 3. Финальный шаг — поиск билетов
@router.message(HotTickets.to_city)
async def hot_finish(msg: types.Message, state: FSMContext):
    if msg.text == "⬅️ Назад в меню":
        await state.clear()
        return await msg.answer("Вы вернулись в главное меню", reply_markup=keyboards.main_menu())

    data = await state.get_data()
    from_code = data.get('from_code')
    from_city_name = data.get('from_city')

    # РЕЖИМ "КУДА УГОДНО"
    if msg.text == "🌍 Куда угодно":
        await msg.answer("🔎 Ищу лучшие варианты по разным направлениям...")
        
        popular_dest = ['LED', 'AER', 'KZN', 'MRV', 'KGD', 'IST', 'DXB']
        
        # Запускаем все запросы одновременно (параллельно)
        tasks = [parse_flights(from_code, d, endpoint="latest") for d in popular_dest]
        results = await asyncio.gather(*tasks)

        all_flights = []
        for res in results:
            flights_data = res.get('data', [])
            if isinstance(flights_data, list):
                # Оставляем только те, что на ближайшую неделю
                hot = [f for f in flights_data if is_date_in_coming_week(f.get('departure_at'))]
                all_flights.extend(hot)

        if not all_flights:
            return await msg.answer("😔 На ближайшую неделю билетов 'куда угодно' не нашлось.")

        # Сортируем по цене и убираем дубликаты городов
        all_flights.sort(key=lambda x: x.get('price', 999999))
        
        unique_flights = []
        seen_cities = set()

        for f in all_flights:
            dest_code = f.get('destination')
            if dest_code not in seen_cities:
                unique_flights.append(f)
                seen_cities.add(dest_code)
            if len(unique_flights) == 3: # Берем топ-3 направления
                break

        response = "🌍 **Топ выгодных направлений:**\n\n"
        for i, f in enumerate(unique_flights, 1):
            dest_iata = f.get('destination')
            dest_name = CITY_NAMES_RU.get(dest_iata, dest_iata)
            response += format_one_way_ticket(f, from_city_name, dest_name, i)

        await msg.answer(response, parse_mode="Markdown", disable_web_page_preview=True)
        return await state.clear()

    # ОБЫЧНЫЙ РЕЖИМ (ПОИСК В КОНКРЕТНЫЙ ГОРОД)
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
        # Если API вернуло список, берем первый, если словарь — сортируем
        if isinstance(flights, list):
            best_flight = flights[0]
    else:
        best_flight = min(hot_now, key=lambda x: x.get('price', 999999))

    response = "🔥 **Самый горячий билет:**\n\n"
    response += format_one_way_ticket(best_flight, from_city_name, msg.text)

    await msg.answer(response, parse_mode="Markdown", disable_web_page_preview=True)
    await state.clear()