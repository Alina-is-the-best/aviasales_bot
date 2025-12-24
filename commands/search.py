# search.py - ОБЪЕДИНЕННЫЙ ФАЙЛ ДЛЯ ПРОСТОГО И СЛОЖНОГО ПОИСКА
import asyncio
from datetime import datetime, timedelta
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)

from infra.keyboards import keyboards
from infra.states import SimpleSearch, ComplexSearch
from infra.keyboards.calendar_kb import build_calendar
from models.repo import filters_repository as filters_repo
from adapters.api.aviasales_api import parse_flights
from models.data.city_codes import get_city_code
from models.repo.tracked_repository import add_tracked
from utils.utils import format_date_for_api, format_one_way_ticket, format_round_trip_ticket

router = Router()

def register(dp):
    dp.include_router(router)

# Глобальная переменная для быстрого сохранения последнего поиска
last_search_data = {}

# ================ ОБЩИЕ ФУНКЦИИ ================

async def filter_flights(flights: list, state_data: dict, user_filters) -> list:
    """Фильтрует список билетов согласно настройкам пользователя."""
    filtered = []
    
    # Безопасное получение limit_price
    limit_price = None
    try:
        # Сначала пробуем из state_data
        price_limit_value = state_data.get('price_limit')
        if price_limit_value:
            # Проверяем, что это число (не строка с текстом)
            if isinstance(price_limit_value, (int, float)):
                limit_price = int(price_limit_value)
            elif isinstance(price_limit_value, str) and price_limit_value.isdigit():
                limit_price = int(price_limit_value)
        
        # Если не нашли в state_data, пробуем из user_filters
        if limit_price is None and user_filters and user_filters.price_limit:
            filter_price = user_filters.price_limit
            if isinstance(filter_price, (int, float)):
                limit_price = int(filter_price)
            elif isinstance(filter_price, str) and filter_price.isdigit():
                limit_price = int(filter_price)
    except (ValueError, TypeError):
        limit_price = None
    
    req_transfers = state_data.get('transfers') or (user_filters.transfers if user_filters else None)

    for f in flights:
        # Фильтр цены
        price = f.get('price', f.get('value', 0))
        if limit_price is not None and limit_price > 0:
            if price > limit_price: 
                continue

        # Фильтр пересадок
        transfers = f.get('transfers', f.get('number_of_changes', 0))
        if req_transfers == 'Только прямой рейс' and transfers > 0: 
            continue
        
        filtered.append(f)
    return filtered

async def _calc_min_date_for_segment(state: FSMContext) -> datetime:
    """Вычисляет минимальную дату для следующего сегмента в сложном маршруте"""
    data = await state.get_data()
    segments = data.get("segments", [])
    if segments:
        try:
            last_date = datetime.strptime(segments[-1]["date"], "%d.%m.%Y")
            return last_date + timedelta(days=1)
        except: 
            pass
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

async def search_complex_route(msg: types.Message, data: dict):
    """Поиск билетов для сложного маршрута"""
    from models.data.city_codes import get_city_code
    from adapters.api.aviasales_api import parse_flights
    from utils.utils import format_one_way_ticket, format_date_for_api
    import asyncio
    
    segments = data.get("segments", [])
    
    if not segments:
        await msg.answer("❌ Нет сегментов для поиска.")
        return
    
    # Собираем запросы для каждого сегмента
    search_tasks = []
    for segment in segments:
        origin = get_city_code(segment['from'])
        destination = get_city_code(segment['to'])
        depart_date = format_date_for_api(segment['date'])
        
        if origin and destination and depart_date:
            search_tasks.append(
                parse_flights(origin, destination, depart_date=depart_date)
            )
        else:
            await msg.answer(f"❌ Не удалось найти код города для {segment['from']} → {segment['to']}")
            return
    
    # Выполняем все запросы параллельно
    await msg.answer("🔄 Ищу билеты для всех сегментов...")
    
    try:
        results = await asyncio.gather(*search_tasks)
        
        # Проверяем результаты
        all_found = True
        flight_options = []
        
        for i, result in enumerate(results):
            segment = segments[i]
            flights = result.get('data', [])
            
            if not flights:
                await msg.answer(f"❌ Не найдено билетов для: {segment['from']} → {segment['to']} на {segment['date']}")
                all_found = False
                break
            
            # Фильтруем по пересадкам, если нужно
            filtered_flights = flights
            if data.get('transfers') == 'Только прямой':
                filtered_flights = [f for f in flights if f.get('transfers', 0) == 0]
            
            if not filtered_flights:
                await msg.answer(f"❌ Нет подходящих билетов (слишком много пересадок) для: {segment['from']} → {segment['to']}")
                all_found = False
                break
            
            # Берем самый дешевый вариант
            cheapest = min(filtered_flights, key=lambda x: x.get('price', float('inf')))
            flight_options.append({
                'segment': segment,
                'flight': cheapest
            })
        
        if all_found and flight_options:
            # Формируем финальный ответ
            total_price = sum(f['flight'].get('price', 0) for f in flight_options)
            
            response = "✅ **Найденные билеты для вашего маршрута:**\n\n"
            
            for i, option in enumerate(flight_options, 1):
                segment = option['segment']
                flight = option['flight']
                response += f"**Сегмент {i}: {segment['from']} → {segment['to']}**\n"
                response += format_one_way_ticket(flight, segment['from'], segment['to'])
                response += "\n"
            
            response += f"💰 **Общая стоимость: {total_price}₽**\n\n"
            response += "💡 *Для каждого сегмента показан самый дешевый вариант.*"
            
            await msg.answer(response, parse_mode="Markdown")
        elif not all_found:
            await msg.answer("😔 Не удалось найти билеты на все сегменты маршрута.")
            
    except Exception as e:
        await msg.answer(f"⚠️ Произошла ошибка при поиске: {str(e)}")
        import traceback
        print(traceback.format_exc())

async def offer_tracking(msg: types.Message, data: dict):
    """Предложить отслеживание цены"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔔 Отслеживать цену", callback_data="track_search")]
    ])
    
    # Сохраняем в глобальную переменную
    global last_search_data
    last_search_data = data.copy()
    
    await msg.answer("Хотите получать уведомления об изменении цены?", reply_markup=kb)

# ================ ОБРАБОТЧИК КНОПКИ "НАЗАД" ================

# Обработка кнопки "Назад в меню" для всех состояний
@router.message(F.text == "⬅️ Назад в меню")
async def back_to_menu_from_search(msg: types.Message, state: FSMContext):
    """Обработка кнопки 'Назад в меню' из любого состояния поиска"""
    await state.clear()
    await msg.answer(
        "Главное меню:",
        reply_markup=keyboards.main_menu()
    )

# ================ ОБРАБОТЧИКИ КАЛЕНДАРЯ ================

@router.callback_query(F.data.startswith("prev_") | F.data.startswith("next_"))
async def calendar_navigation(callback: types.CallbackQuery, state: FSMContext):
    """Универсальный обработчик навигации календаря"""
    current_state = await state.get_state()
    
    # Получаем данные из callback
    action, year, month = callback.data.split("_")
    year, month = int(year), int(month)
    
    min_date = None
    
    # Определяем min_date в зависимости от состояния
    if current_state == SimpleSearch.dates.state:
        # Для выбора даты в одну сторону - нет ограничений
        pass
    elif current_state == SimpleSearch.depart_date.state:
        # Для даты вылета - нет ограничений
        pass
    elif current_state == SimpleSearch.return_date.state:
        # Для даты возвращения - ограничение: после даты вылета
        data = await state.get_data()
        if "depart_date" in data and data["depart_date"]:
            try:
                min_date = datetime.strptime(data["depart_date"], "%d.%m.%Y")
            except:
                pass
    elif current_state == ComplexSearch.segment_date.state:
        # Для сложного маршрута - ограничение из min_date
        data = await state.get_data()
        min_date = data.get("min_date")
    
    # Обновляем календарь
    await callback.message.edit_reply_markup(
        reply_markup=build_calendar(year, month, min_date=min_date)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("date_"))
async def date_selection(callback: types.CallbackQuery, state: FSMContext):
    """Универсальный обработчик выбора даты"""
    _, year, month, day = callback.data.split("_")
    selected_date = f"{day.zfill(2)}.{month.zfill(2)}.{year}"
    current_state = await state.get_state()
    
    # Для простого поиска (в одну сторону)
    if current_state == SimpleSearch.dates.state:
        await state.update_data(dates=selected_date)
        await finish_search_one_way(callback.message, state)
    
    # Для простого поиска (дата вылета туда-обратно)
    elif current_state == SimpleSearch.depart_date.state:
        await state.update_data(depart_date=selected_date)
        await state.set_state(SimpleSearch.return_date)
        
        dt = datetime.strptime(selected_date, "%d.%m.%Y")
        await callback.message.edit_text(f"Вылет: {selected_date}.\n📅 Выберите дату возвращения:")
        await callback.message.edit_reply_markup(
            reply_markup=build_calendar(dt.year, dt.month, min_date=dt)
        )
    
    # Для простого поиска (дата возвращения)
    elif current_state == SimpleSearch.return_date.state:
        await state.update_data(return_date=selected_date)
        await finish_search_round_trip(callback.message, state)
    
    # Для сложного поиска (дата сегмента)
    elif current_state == ComplexSearch.segment_date.state:
        # Извлекаем дату из callback (формат date_YYYY_MM_DD)
        vals = callback.data.split("_")
        date_selected = f"{vals[3].zfill(2)}.{vals[2].zfill(2)}.{vals[1]}"

        data = await state.get_data()
        segments = data.get("segments", [])
        
        segment = {
            "from": data["segment_from"],
            "to": data["segment_to"],
            "date": date_selected
        }
        segments.append(segment)
        await state.update_data(segments=segments)

        # 1. Удаляем inline-клавиатуру календаря
        await callback.message.edit_reply_markup(reply_markup=None)
        
        # 2. Отправляем новое сообщение с reply-клавиатурой
        await callback.message.answer(
            f"✅ Добавлен сегмент: {segment['from']} → {segment['to']} | {segment['date']}\n\nЧто дальше?",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="➕ Добавить сегмент")],
                    [KeyboardButton(text="✔ Завершить маршрут")],
                    [KeyboardButton(text="⬅️ Назад в меню")]
                ],
                resize_keyboard=True
            )
        )
        
        await state.set_state(ComplexSearch.add_more)
    
    await callback.answer()

# ================ НАЧАЛО ПОИСКА ================

@router.message(F.text == "Найти билеты")
async def start_search(msg: types.Message, state: FSMContext):
    await state.clear() # Очищаем старые данные
    await msg.answer(
        "Выберите тип маршрута:", 
        reply_markup=keyboards.route_type_menu() # Показываем кнопки Простой/Сложный
    )

# ================ ПРОСТОЙ ПОИСК ================

@router.message(F.text == "Простой маршрут")
async def process_simple_route(msg: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(SimpleSearch.from_city)
    await msg.answer(
        "🛫 Откуда вылетаем?", 
        reply_markup=keyboards.back_to_main()
    )

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
        now = datetime.now()
        await msg.answer("📅 Выберите дату вылета:", reply_markup=build_calendar(now.year, now.month))
    elif msg.text == "Туда-обратно":
        await state.update_data(trip_type="round_trip")
        await state.set_state(SimpleSearch.depart_date)
        now = datetime.now()
        await msg.answer("📅 Выберите дату вылета:", reply_markup=build_calendar(now.year, now.month))
    else:
        return await msg.answer("Выберите вариант на кнопках.")

# Функции завершения поиска для простого маршрута
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
    
    # Предлагаем отслеживание
    await offer_tracking(msg, {**data, 'trip_type': 'one_way'})
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
    
    # Предлагаем отслеживание
    await offer_tracking(msg, {**data, 'trip_type': 'round_trip'})
    await state.clear()

# ================ СЛОЖНЫЙ ПОИСК ================

@router.message(F.text == "Сложный маршрут")
async def start_complex(msg: types.Message, state: FSMContext):
    await state.clear() 
    await state.update_data(segments=[])
    await state.set_state(ComplexSearch.segment_from)
    await msg.answer("Введите город вылета для первого сегмента:", reply_markup=keyboards.back_to_main())

@router.message(ComplexSearch.segment_from)
async def segment_from(msg: types.Message, state: FSMContext):
    await state.update_data(segment_from=msg.text)
    await state.set_state(ComplexSearch.segment_to)
    await msg.answer(f"Из {msg.text} летим куда?\nВведите город прилёта:", reply_markup=keyboards.back_to_main())

@router.message(ComplexSearch.segment_to)
async def segment_to(msg: types.Message, state: FSMContext):
    await state.update_data(segment_to=msg.text)
    now = datetime.now()
    min_date = await _calc_min_date_for_segment(state)
    await state.update_data(min_date=min_date)
    await state.set_state(ComplexSearch.segment_date)
    await msg.answer("Выберите дату сегмента:", reply_markup=build_calendar(now.year, now.month, min_date=min_date))

# --- КНОПКИ "ДОБАВИТЬ" / "ЗАВЕРШИТЬ" ---
@router.message(ComplexSearch.add_more)
async def add_more(msg: types.Message, state: FSMContext):
    if msg.text == "➕ Добавить сегмент":
        data = await state.get_data()
        # АВТОПОДСТАНОВКА: город прилета становится городом вылета
        last_to = data["segments"][-1]["to"]
        await state.update_data(segment_from=last_to)
        await state.set_state(ComplexSearch.segment_to)
        return await msg.answer(f"Следующий вылет из {last_to}. Введите город прилёта:", reply_markup=keyboards.back_to_main())

    if msg.text == "✔ Завершить маршрут":
        await state.set_state(ComplexSearch.baggage)
        return await msg.answer("Нужен багаж?", reply_markup=keyboards.baggage_kb())
    
    await msg.answer("Используйте кнопки под полем ввода.")

@router.message(ComplexSearch.baggage)
async def baggage_selection(msg: types.Message, state: FSMContext):
    if msg.text not in ["С багажом", "Без багажа"]:
        return await msg.answer("Выберите вариант с кнопок.")
    
    await state.update_data(baggage=msg.text)
    await state.set_state(ComplexSearch.transfers)
    await msg.answer("Пересадки:", reply_markup=keyboards.transfers_kb())

@router.message(ComplexSearch.transfers)
async def transfers_selection(msg: types.Message, state: FSMContext):
    if msg.text not in ["Только прямой", "Любой подойдет"]:
        return await msg.answer("Выберите вариант с кнопок.")
    
    await state.update_data(transfers=msg.text)
    await state.set_state(ComplexSearch.price_limit)
    await msg.answer("Введите максимальную цену (или 0, если без ограничений):")

@router.message(ComplexSearch.price_limit)
async def price_limit_selection(msg: types.Message, state: FSMContext):
    try:
        price = int(msg.text)
        await state.update_data(price_limit=price)
        
        # Собираем все данные
        data = await state.get_data()
        
        # Формируем ответ
        response = "🎫 **Ваш сложный маршрут:**\n\n"
        for i, segment in enumerate(data["segments"], 1):
            response += f"{i}. {segment['from']} → {segment['to']} | {segment['date']}\n"
        
        response += f"\nФильтры:\n"
        response += f"• Багаж: {data.get('baggage', 'Не указано')}\n"
        response += f"• Пересадки: {data.get('transfers', 'Не указано')}\n"
        response += f"• Макс. цена: {data.get('price_limit', 0)}₽\n\n"
        
        # ПОИСК БИЛЕТОВ
        response += "🔎 Ищу билеты..."
        await msg.answer(response, parse_mode="Markdown")
        
        # ВЫПОЛНЯЕМ ПОИСК
        await search_complex_route(msg, data)
        
        await state.clear()
        
    except ValueError:
        await msg.answer("Пожалуйста, введите число (например: 50000)")

# ================ ОТСЛЕЖИВАНИЕ ================

@router.callback_query(F.data == "track_search")
async def track_search_callback(callback: types.CallbackQuery):
    global last_search_data
    if not last_search_data:
        return await callback.answer("Ошибка: данные поиска устарели.", show_alert=True)
    
    # Определяем даты
    if last_search_data.get("dates"):  # one-way
        date_from = last_search_data["dates"]
        date_to = ""
    elif last_search_data.get("depart_date"):  # round-trip
        date_from = last_search_data.get("depart_date", "")
        date_to = last_search_data.get("return_date", "")
    else:  # complex search (используем первый сегмент)
        segments = last_search_data.get("segments", [])
        if segments:
            date_from = segments[0]["date"]
            date_to = segments[-1]["date"] if len(segments) > 1 else ""
        else:
            date_from = ""
            date_to = ""
    
    await add_tracked(
        user_id=callback.from_user.id,
        from_city=last_search_data.get("from_city", ""),
        to_city=last_search_data.get("to_city", ""),
        date_from=date_from,
        date_to=date_to,
        baggage=last_search_data.get("baggage", "Не указано"),
        transfers=last_search_data.get("transfers", "Не указано"),
        price_limit=last_search_data.get("price_limit", "0")
    )
    
    await callback.answer("✅ Билет добавлен в отслеживаемые!", show_alert=True)
    await callback.message.answer("Билет добавлен в отслеживаемые", reply_markup=keyboards.main_menu())