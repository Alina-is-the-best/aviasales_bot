import asyncio
from datetime import datetime
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from infra.keyboards import keyboards
from infra.states import SimpleSearch
from infra.keyboards.calendar_kb import build_calendar
from models.repo import filters_repository as filters_repo
from adapters.api.aviasales_api import parse_flights
from models.data.city_codes import get_city_code
from utils.utils import format_date_for_api, format_one_way_ticket, format_round_trip_ticket

router = Router()

def register(dp):
    dp.include_router(router)

# Глобальная переменная для быстрого сохранения последнего поиска
last_search_data = {}

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

async def filter_flights(flights: list, state_data: dict, user_filters) -> list:
    """Фильтрует список билетов согласно настройкам пользователя."""
    filtered = []
    limit_price = state_data.get('price_limit') or (user_filters.price_limit if user_filters else None)
    req_transfers = state_data.get('transfers') or (user_filters.transfers if user_filters else None)

    for f in flights:
        # Фильтр цены
        price = f.get('price', f.get('value', 0))
        if limit_price and int(limit_price) > 0:
            if price > int(limit_price): continue

        # Фильтр пересадок
        transfers = f.get('transfers', f.get('number_of_changes', 0))
        if req_transfers == 'Только прямой рейс' and transfers > 0: continue
        
        filtered.append(f)
    return filtered

async def update_calendar_view(callback: types.CallbackQuery, state: FSMContext):
    _, y, m = callback.data.split("_")
    y, m = int(y), int(m)
    data = await state.get_data()
    min_date = None
    
    if "depart_date" in data and data["depart_date"]:
        try:
            min_date = datetime.strptime(data["depart_date"], "%d.%m.%Y")
        except: min_date = None

    await callback.message.edit_reply_markup(
        reply_markup=build_calendar(y, m, min_date=min_date)
    )
    await callback.answer()

# --- ХЕНДЛЕРЫ ---

@router.message(F.text == "Найти билеты")
async def start_search(msg: types.Message, state: FSMContext):
    await state.set_state(SimpleSearch.from_city)
    await msg.answer("🛫 Откуда вылетаем?", reply_markup=keyboards.back_to_main())

@router.message(SimpleSearch.from_city)
async def select_origin(msg: types.Message, state: FSMContext):
    code = get_city_code(msg.text)
    if not code:
        return await msg.answer("❌ Город не найден. Попробуйте снова.")
    await state.update_data(from_city=msg.text, from_code=code)
    await state.set_state(SimpleSearch.to_city)
    await msg.answer(f"Куда летим из {msg.text}?")

@router.message(SimpleSearch.to_city)
async def select_destination(msg: types.Message, state: FSMContext):
    code = get_city_code(msg.text)
    if not code:
        return await msg.answer("❌ Город не найден.")
    await state.update_data(to_city=msg.text, to_code=code)
    await state.set_state(SimpleSearch.trip_type)
    await msg.answer("Тип маршрута:", reply_markup=keyboards.trip_type_kb())

@router.message(SimpleSearch.trip_type)
async def select_trip_type(msg: types.Message, state: FSMContext):
    if msg.text == "В одну сторону":
        await state.update_data(trip_type="one_way")
        await state.set_state(SimpleSearch.dates)
    elif msg.text == "Туда-обратно":
        await state.update_data(trip_type="round_trip")
        await state.set_state(SimpleSearch.depart_date)
    else:
        return await msg.answer("Выберите вариант на кнопках.")

    now = datetime.now()
    await msg.answer("📅 Выберите дату вылета:", reply_markup=build_calendar(now.year, now.month))

@router.callback_query(F.data.startswith("prev_"))
@router.callback_query(F.data.startswith("next_"))
async def calendar_nav(callback: types.CallbackQuery, state: FSMContext):
    await update_calendar_view(callback, state)

@router.callback_query(F.data.startswith("date_"))
async def date_selection(callback: types.CallbackQuery, state: FSMContext):
    _, year, month, day = callback.data.split("_")
    selected_date = f"{day.zfill(2)}.{month.zfill(2)}.{year}"
    current_state = await state.get_state()
    
    if current_state == SimpleSearch.dates:
        await state.update_data(dates=selected_date)
        await finish_search_one_way(callback.message, state)
    elif current_state == SimpleSearch.depart_date:
        await state.update_data(depart_date=selected_date)
        await state.set_state(SimpleSearch.return_date)
        dt = datetime.strptime(selected_date, "%d.%m.%Y")
        await callback.message.edit_text(f"Вылет: {selected_date}.\n📅 Выберите дату возвращения:")
        await callback.message.edit_reply_markup(reply_markup=build_calendar(dt.year, dt.month, min_date=dt))
    elif current_state == SimpleSearch.return_date:
        await state.update_data(return_date=selected_date)
        await finish_search_round_trip(callback.message, state)
    await callback.answer()

# --- ФИНАЛЬНЫЕ ФУНКЦИИ ПОИСКА ---

async def finish_search_one_way(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    api_date = format_date_for_api(data['dates'])
    await msg.answer(f"🔎 Ищу билеты {data['from_city']} → {data['to_city']}...")
    
    result = await parse_flights(origin=data['from_code'], destination=data['to_code'], depart_date=api_date)
    
    if not result.get('data'):
        await msg.answer("😔 Билеты не найдены.")
        return await state.clear()

    user_filters = await filters_repo.get_filters(msg.chat.id)
    flights = await filter_flights(result['data'], data, user_filters)
    
    if not flights:
        await msg.answer("❌ Нет билетов под ваши фильтры.")
        return await state.clear()

    flights.sort(key=lambda x: x.get('price', float('inf')))
    response = "🎫 **Найденные билеты:**\n\n"
    for i, flight in enumerate(flights[:5], 1):
        response += format_one_way_ticket(flight, data['from_city'], data['to_city'], i)
    
    await msg.answer(response, parse_mode="Markdown", disable_web_page_preview=True)
    global last_search_data
    last_search_data = {**data, 'trip_type': 'one_way'}
    await offer_tracking(msg)
    await state.clear()

async def finish_search_round_trip(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    date_there = format_date_for_api(data['depart_date'])
    date_back = format_date_for_api(data['return_date'])
    await msg.answer("🔎 Ищу билеты туда-обратно...")
    
    res_there, res_back = await asyncio.gather(
        parse_flights(data['from_code'], data['to_code'], date_there),
        parse_flights(data['to_code'], data['from_code'], date_back)
    )
    
    if not res_there.get('data') or not res_back.get('data'):
        await msg.answer("❌ Не нашли билеты в одну из сторон.")
        return await state.clear()

    flights_there = sorted(res_there['data'], key=lambda x: x.get('price', 0))[:3]
    flights_back = sorted(res_back['data'], key=lambda x: x.get('price', 0))[:3]
    
    response = f"🎫 **Билеты {data['from_city']} ↔ {data['to_city']}:**\n\n"
    count = 1
    for ft in flights_there:
        for fb in flights_back:
            if count > 3: break
            response += format_round_trip_ticket(ft, fb, data['from_city'], data['to_city'], count)
            count += 1
            
    await msg.answer(response, parse_mode="Markdown", disable_web_page_preview=True)
    global last_search_data
    last_search_data = {**data, 'trip_type': 'round_trip'}
    await offer_tracking(msg)
    await state.clear()

async def offer_tracking(msg: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔔 Отслеживать цену", callback_data="track_search")]
    ])
    await msg.answer("Хотите получать уведомления об изменении цены?", reply_markup=kb)

@router.callback_query(F.data == "track_search")
async def track_search_callback(callback: types.CallbackQuery):
    from repo.tracked_repository import add_tracked
    if not last_search_data:
        return await callback.answer("Ошибка: данные поиска устарели.")
    
    # Логика сохранения в БД
    await add_tracked(
        user_id=callback.from_user.id,
        from_city=last_search_data["from_city"],
        to_city=last_search_data["to_city"],
        date_from=last_search_data.get("dates") or last_search_data.get("depart_date"),
        date_to=last_search_data.get("return_date", ""),
        price_limit=last_search_data.get("price_limit", "")
    )
    await callback.answer("✅ Добавлено в отслеживаемые!", show_alert=True)