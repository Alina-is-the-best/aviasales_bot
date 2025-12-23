import asyncio
from datetime import datetime
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import keyboards
from states import SimpleSearch
<<<<<<< Updated upstream
from calendar_kb import build_calendar
import filters_repository as filters_repo
from parser.aviasales_api import parse_flights
from city_codes import get_city_code
from datetime import datetime, timedelta
=======
from keyboards.calendar_kb import build_calendar
from repo import filters_repository as filters_repo
from api.aviasales_api import parse_flights
from data.city_codes import get_city_code
from utils.utils import format_date_for_api, format_one_way_ticket, format_round_trip_ticket
>>>>>>> Stashed changes

router = Router()

def register(dp):
    dp.include_router(router)

# Глобальная переменная для кнопки "отслеживать"
last_search_data = {}

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (Logic Layer) ---

async def filter_flights(flights: list, state_data: dict, user_filters) -> list:
    """Фильтрует список билетов согласно настройкам пользователя и стейту."""
    filtered = []
    
    # Определяем лимиты (приоритет: данные поиска > сохраненные фильтры)
    limit_price = state_data.get('price_limit') or (user_filters.price_limit if user_filters else None)
    req_baggage = state_data.get('baggage') or (user_filters.baggage if user_filters else None)
    req_transfers = state_data.get('transfers') or (user_filters.transfers if user_filters else None)

    for f in flights:
        # 1. Фильтр цены
        price = f.get('price', f.get('value', 0))
        if limit_price and int(limit_price) > 0:
            if price > int(limit_price):
                continue

        # 2. Фильтр пересадок
        transfers = f.get('transfers', f.get('number_of_changes', 0))
        if req_transfers == 'direct' and transfers > 0:
            continue
        if req_transfers == '1_stop' and transfers > 1:
            continue

        # 3. Фильтр багажа (API Aviasales в бесплатной версии не всегда дает данные о багаже точно,
        # но если поле есть, используем его)
        # has_baggage = f.get('has_baggage', True) 
        # Здесь логика зависит от того, что возвращает API. Оставим заглушку пока.
        
        filtered.append(f)
    
    return filtered

async def update_calendar_view(callback: types.CallbackQuery, state: FSMContext):
    """Обновляет сообщение с календарем (DRY для prev/next)."""
    _, y, m = callback.data.split("_")
    y, m = int(y), int(m)
    
    data = await state.get_data()
    min_date = None
    
    # Если выбираем дату возврата, блокируем дни до даты вылета
    if "depart_date" in data and data["depart_date"]:
        try:
            min_date = datetime.strptime(data["depart_date"], "%d.%m.%Y")
        except ValueError:
            min_date = None

<<<<<<< Updated upstream
        print(f"After filtering: {len(filtered_flights)} flights")

        if not filtered_flights:
            await msg.answer("❌ После применения фильтров билеты не найдены.")
            await state.clear()
            return

        # Сортируем по цене
        sorted_flights = sorted(
            filtered_flights,
            key=lambda x: x.get('value', x.get('price', float('inf')))  # Используем 'value' для dates endpoint
        )[:5]
        
        response_text = "🎫 Найденные билеты:\n\n"
        
        for i, flight in enumerate(sorted_flights, 1):
            # Для v3 API структура отличается
            price = flight.get('price', '?')
            airline = flight.get('airline', flight.get('airline_iata', 'Неизвестно'))
            flight_number = flight.get('flight_number', '?')
            
            # Форматируем дату вылета
            departure_at = flight.get('departure_at', '')
            departure_formatted = '?'
            if departure_at:
                try:
                    # Преобразуем из "2026-01-02T10:20:00+03:00" в "02.01.2026 10:20"
                    if 'T' in departure_at:
                        date_part = departure_at.split('T')[0]
                        time_part = departure_at.split('T')[1].split('+')[0][:5]
                        year, month, day = date_part.split('-')
                        departure_formatted = f"{day}.{month}.{year} {time_part}"
                    else:
                        # Просто дата без времени
                        year, month, day = departure_at.split('-')
                        departure_formatted = f"{day}.{month}.{year}"
                except Exception as e:
                    print(f"Error formatting departure date: {e}")
                    departure_formatted = departure_at
            
            # Длительность В ОДНУ СТОРОНУ
            duration = flight.get('duration', flight.get('duration_to', 0))
            if duration:
                hours = duration // 60
                minutes = duration % 60
                duration_text = f"{hours}ч {minutes}м"
            else:
                duration_text = "?"
            
            # Количество пересадок (для v3 API)
            transfers = flight.get('transfers', flight.get('number_of_changes', 0))
            transfers_text = "прямой" if transfers == 0 else f"{transfers} пересадки"
            
            response_text += (
                f"{i}. {data['from_city']} → {data['to_city']}\n"
                f"   💰 Цена: {price}₽\n"
                f"   🏢 Авиакомпания: {airline}\n"
                f"   ✈️ Вылет: {departure_formatted}\n"
                f"   ⏱ Длительность: {duration_text}\n"
                f"   🔄 {transfers_text}\n"
                f"   🔢 Номер рейса: {flight_number}\n\n"
            )
        
        await msg.answer(response_text)
        
        # Предлагаем добавить в отслеживаемые
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="➕ Добавить в отслеживаемые",
                callback_data="track_search"
            )]
        ])
        
        await msg.answer("Хотите отслеживать такие билеты?", reply_markup=inline_kb)
        
    except Exception as e:
        await msg.answer(f"⚠️ Произошла ошибка при поиске: {str(e)}")
        import traceback
        print(traceback.format_exc())
    
    await state.clear()


# --------------------------------------------------------------
# Финальный шаг поиска туда-обратно с парсингом
# --------------------------------------------------------------

async def finish_search_round_trip(msg: types.Message, state: FSMContext):
    """Завершает поиск для маршрута 'Туда-обратно'"""
    data = await state.get_data()
    
    print(f"=== ROUND-TRIP DEBUG ===")
    print(f"Data: {data}")
    
    # Сохраняем данные для кнопки
    global last_search_data
    last_search_data = data.copy()
    last_search_data['trip_type'] = 'round_trip'
    
    # Получаем постоянные фильтры пользователя
    user_filters = await filters_repo.get_filters(msg.from_user.id)
    
    # Получаем коды городов
    from_city_code = get_city_code(data['from_city'])
    to_city_code = get_city_code(data['to_city'])
    
    print(f"Коды: {from_city_code} -> {to_city_code}")
    
    # Получаем даты
    depart_date = data.get("depart_date")
    return_date = data.get("return_date")
    
    if not depart_date or not return_date:
        await msg.answer("❌ Ошибка: не найдены даты туда и/или обратно.")
        await state.clear()
        return
    
    # Форматируем даты для API
    try:
        day, month, year = depart_date.split('.')
        api_depart_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        day, month, year = return_date.split('.')
        api_return_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        print(f"Даты для API: туда={api_depart_date}, обратно={api_return_date}")
        
    except Exception as e:
        await msg.answer(f"❌ Ошибка формата даты: {e}")
        await state.clear()
        return
    
    await msg.answer(f"🔍 Ищу билеты {data['from_city']} → {data['to_city']} на {depart_date} - {return_date}...")
    
    try:
        # Ищем билеты ТУДА
        print(f"=== ПОИСК ТУДА: {from_city_code} -> {to_city_code} на {api_depart_date} ===")
        result_there = await parse_flights(
            origin=from_city_code,
            destination=to_city_code,
            depart_date=api_depart_date,
            currency="RUB",
            endpoint="latest"
        )
        
        print(f"Результат ТУДА: has_data={bool(result_there.get('data'))}, error={result_there.get('error')}")
        
        # Ищем билеты ОБРАТНО
        print(f"=== ПОИСК ОБРАТНО: {to_city_code} -> {from_city_code} на {api_return_date} ===")
        result_back = await parse_flights(
            origin=to_city_code,
            destination=from_city_code,
            depart_date=api_return_date,
            currency="RUB",
            endpoint="latest"
        )
        
        print(f"Результат ОБРАТНО: has_data={bool(result_back.get('data'))}, error={result_back.get('error')}")
        
        # Если оба направления найдены
        if result_there.get('data') and result_back.get('data'):
            flights_there_raw = result_there['data']
            flights_back_raw = result_back['data']
            
            if isinstance(flights_there_raw, list) and isinstance(flights_back_raw, list):
                # ВАЖНО: проверяем, есть ли вообще билеты на эти даты
                if not flights_there_raw or not flights_back_raw:
                    await msg.answer("❌ На указанные даты нет доступных билетов.")
                    await state.clear()
                    return
                
                # Берем первые 3 самых дешевых билета в каждом направлении
                cheapest_there = sorted(flights_there_raw, key=lambda x: x.get('price', float('inf')))[:3]
                cheapest_back = sorted(flights_back_raw, key=lambda x: x.get('price', float('inf')))[:3]
                
                # Проверяем, соответствуют ли билеты фильтру "Только прямой"
                direct_there = [f for f in cheapest_there if f.get('transfers', 0) == 0]
                direct_back = [f for f in cheapest_back if f.get('transfers', 0) == 0]
                
                # Если выбран фильтр "Только прямой", но прямых рейсов нет
                if data.get('transfers') == "Только прямой" and (not direct_there or not direct_back):
                    warning = "⚠️ Прямых рейсов на выбранные даты не найдено.\n"
                    if not direct_there:
                        warning += f"• На {depart_date} из {data['from_city']} в {data['to_city']} только с пересадками\n"
                    if not direct_back:
                        warning += f"• На {return_date} из {data['to_city']} в {data['from_city']} только с пересадками\n"
                    warning += "\nПоказать лучшие варианты с пересадками?"
                    
                    # Создаем клавиатуру для выбора
                    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="✅ Да, показать", callback_data="show_with_transfers")],
                        [InlineKeyboardButton(text="❌ Нет, изменить даты", callback_data="change_dates")]
                    ])
                    
                    await msg.answer(warning, reply_markup=inline_kb)
                    
                    # Сохраняем данные для callback
                    await state.update_data(
                        cheapest_there=cheapest_there,
                        cheapest_back=cheapest_back,
                        show_with_transfers=True
                    )
                    return
                
                # Если фильтр "Только прямой" и есть прямые рейсы, или фильтр "Любой подойдет"
                # Формируем список билетов для показа
                flights_to_show_there = direct_there if data.get('transfers') == "Только прямой" else cheapest_there
                flights_to_show_back = direct_back if data.get('transfers') == "Только прямой" else cheapest_back
                
                if not flights_to_show_there or not flights_to_show_back:
                    await msg.answer("❌ После применения фильтров не осталось подходящих билетов.")
                    await state.clear()
                    return
                
                # Формируем результат
                response_text = f"🎫 Найденные билеты {data['from_city']} ↔ {data['to_city']}:\n\n"
                
                # Покажем несколько комбинаций (самые дешевые)
                for i, flight_there in enumerate(flights_to_show_there[:2], 1):
                    for j, flight_back in enumerate(flights_to_show_back[:2], 1):
                        if i > 1 and j > 1:  # Ограничим количество комбинаций
                            break
                        
                        total_price = flight_there.get('price', 0) + flight_back.get('price', 0)
                        
                        # Проверяем ценовой фильтр
                        price_limit = None
                        if data.get('price_limit') and str(data.get('price_limit')).isdigit():
                            price_limit = int(data.get('price_limit'))
                        elif user_filters.price_limit and user_filters.price_limit.isdigit():
                            price_limit = int(user_filters.price_limit)
                        
                        if price_limit and total_price > price_limit:
                            continue
                        
                        # Форматируем даты
                        departure_at = flight_there.get('departure_at', '')
                        departure_formatted = depart_date
                        if departure_at:
                            try:
                                if 'T' in departure_at:
                                    date_part = departure_at.split('T')[0]
                                    time_part = departure_at.split('T')[1].split('+')[0][:5]
                                    year, month, day = date_part.split('-')
                                    departure_formatted = f"{day}.{month}.{year} {time_part}"
                                else:
                                    date_part = departure_at
                                    time_part = ""
                                    year, month, day = date_part.split('-')
                                    departure_formatted = f"{day}.{month}.{year}"
                            except:
                                pass
                        
                        return_at = flight_back.get('departure_at', '')
                        return_formatted = return_date
                        if return_at:
                            try:
                                if 'T' in return_at:
                                    date_part = return_at.split('T')[0]
                                    time_part = return_at.split('T')[1].split('+')[0][:5]
                                    year, month, day = date_part.split('-')
                                    return_formatted = f"{day}.{month}.{year} {time_part}"
                                else:
                                    date_part = return_at
                                    time_part = ""
                                    year, month, day = date_part.split('-')
                                    return_formatted = f"{day}.{month}.{year}"
                            except:
                                pass
                        
                        # Информация о пересадках
                        transfers_there = flight_there.get('transfers', 0)
                        transfers_back = flight_back.get('transfers', 0)
                        
                        transfers_there_text = "прямой" if transfers_there == 0 else f"{transfers_there} пересадка" + ("и" if transfers_there > 1 else "")
                        transfers_back_text = "прямой" if transfers_back == 0 else f"{transfers_back} пересадка" + ("и" if transfers_back > 1 else "")
                        
                        response_text += (
                            f"{i}.💰 Общая цена: {total_price}₽ (туда: {flight_there.get('price', 0)}₽, обратно: {flight_back.get('price', 0)}₽)\n"
                            f"   ✈️ Туда: {flight_there.get('airline', 'Неизвестно')} рейс {flight_there.get('flight_number', '?')}\n"
                            f"         {departure_formatted} ({transfers_there_text})\n"
                            f"   🏠 Обратно: {flight_back.get('airline', 'Неизвестно')} рейс {flight_back.get('flight_number', '?')}\n"
                            f"         {return_formatted} ({transfers_back_text})\n\n"
                        )
                
                if len(response_text) > 50:  # Если есть результаты
                    await msg.answer(response_text)
                    
                    # Предлагаем добавить в отслеживаемые
                    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(
                            text="➕ Добавить в отслеживаемые",
                            callback_data="track_search"
                        )]
                    ])
                    
                    await msg.answer("Хотите отслеживать такие билеты?", reply_markup=inline_kb)
                else:
                    await msg.answer("❌ Не найдено подходящих билетов по указанным фильтрам.")
                
            else:
                await msg.answer("❌ API вернул данные в неожиданном формате.")
        else:
            # Если не найдены билеты в одном из направлений
            error_msg = "❌ Не удалось найти билеты:"
            if not result_there.get('data'):
                error_msg += f"\n• Нет билетов ТУДА на {depart_date}"
            if not result_back.get('data'):
                error_msg += f"\n• Нет билетов ОБРАТНО на {return_date}"
            
            await msg.answer(error_msg)
            
            # Предложим поискать другие даты
            await msg.answer("Попробуйте выбрать другие даты для поиска.")
        
    except Exception as e:
        await msg.answer(f"⚠️ Произошла ошибка при поиске: {str(e)}")
        import traceback
        print(traceback.format_exc())
    
    await state.clear()

# Добавьте этот обработчик для callback "show_with_transfers"
@router.callback_query(F.data == "show_with_transfers")
async def show_flights_with_transfers(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    if not data.get('cheapest_there') or not data.get('cheapest_back'):
        await callback.answer("❌ Данные утеряны.")
        return
    
    cheapest_there = data['cheapest_there']
    cheapest_back = data['cheapest_back']
    
    # Формируем результат с пересадками
    response_text = f"🎫 Билеты с пересадками:\n\n"
    
    # Покажем первые 2 комбинации
    for i, flight_there in enumerate(cheapest_there[:2], 1):
        for j, flight_back in enumerate(cheapest_back[:2], 1):
            if i > 1 and j > 1:
                break
            
            total_price = flight_there.get('price', 0) + flight_back.get('price', 0)
            
            # Форматируем даты
            departure_at = flight_there.get('departure_at', '')
            departure_formatted = data.get('depart_date', '?')
            if departure_at:
                try:
                    if 'T' in departure_at:
                        date_part = departure_at.split('T')[0]
                        time_part = departure_at.split('T')[1].split('+')[0][:5]
                        year, month, day = date_part.split('-')
                        departure_formatted = f"{day}.{month}.{year} {time_part}"
                except:
                    pass
            
            return_at = flight_back.get('departure_at', '')
            return_formatted = data.get('return_date', '?')
            if return_at:
                try:
                    if 'T' in return_at:
                        date_part = return_at.split('T')[0]
                        time_part = return_at.split('T')[1].split('+')[0][:5]
                        year, month, day = date_part.split('-')
                        return_formatted = f"{day}.{month}.{year} {time_part}"
                except:
                    pass
            
            # Информация о пересадках
            transfers_there = flight_there.get('transfers', 0)
            transfers_back = flight_back.get('transfers', 0)
            
            transfers_there_text = "прямой" if transfers_there == 0 else f"{transfers_there} пересадка" + ("и" if transfers_there > 1 else "")
            transfers_back_text = "прямой" if transfers_back == 0 else f"{transfers_back} пересадка" + ("и" if transfers_back > 1 else "")
            
            response_text += (
                f"{i}.💰 Общая цена: {total_price}₽ (туда: {flight_there.get('price', 0)}₽, обратно: {flight_back.get('price', 0)}₽)\n"
                f"   ✈️ Туда: {flight_there.get('airline', 'Неизвестно')} рейс {flight_there.get('flight_number', '?')}\n"
                f"         {departure_formatted} ({transfers_there_text})\n"
                f"   🏠 Обратно: {flight_back.get('airline', 'Неизвестно')} рейс {flight_back.get('flight_number', '?')}\n"
                f"         {return_formatted} ({transfers_back_text})\n\n"
            )
    
    await callback.message.answer(response_text)
    
    # Предлагаем добавить в отслеживаемые
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="➕ Добавить в отслеживаемые",
            callback_data="track_search"
        )]
    ])
    
    await callback.message.answer("Хотите отслеживать такие билеты?", reply_markup=inline_kb)
    
    await callback.answer()
    await state.clear()

@router.callback_query(F.data == "change_dates")
async def change_dates_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Выберите другие даты из меню.")
    await state.clear()
    await callback.message.answer("Главное меню:", reply_markup=keyboards.main_menu())

# --------------------------------------------------------------
# Обработчик кнопки "Добавить в отслеживаемые"
# --------------------------------------------------------------
@router.callback_query(F.data == "track_search")
async def track_search_result(callback: types.CallbackQuery):
    global last_search_data
    
    if not last_search_data:
        await callback.answer("❌ Не удалось добавить. Данные утеряны.")
        return
    
    try:
        # Импортируем здесь, чтобы избежать циклических импортов
        from tracked_repository import add_tracked
        
        # Определяем тип маршрута
        is_one_way = last_search_data.get('trip_type') == 'one_way'
        date_to = "" if is_one_way else last_search_data.get("return_date", "")
        
        await add_tracked(
            user_id=callback.from_user.id,
            from_city=last_search_data["from_city"],
            to_city=last_search_data["to_city"],
            date_from=last_search_data.get("dates") or last_search_data.get("depart_date"),
            date_to=date_to,
            baggage=last_search_data.get("baggage", "Как угодно"),
            transfers=last_search_data.get("transfers", "Любой подойдет"),
            price_limit=last_search_data.get("price_limit", "")
        )
        
        await callback.answer("✅ Билет добавлен в отслеживаемые!", show_alert=True)
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}")
        print(f"Ошибка при добавлении в отслеживаемые: {e}")

# ------------------------------------------------
# ВЫБОР ТИПА МАРШРУТА
# ------------------------------------------------
@router.message(F.text == "Найти билеты")
async def choose_route_type(msg: types.Message):
    await msg.answer(
        "Выберите тип маршрута:",
        reply_markup=keyboards.route_type_menu()
=======
    await callback.message.edit_reply_markup(
        reply_markup=build_calendar(y, m, min_date=min_date)
>>>>>>> Stashed changes
    )
    await callback.answer()


# --- ХЕНДЛЕРЫ (Presentation Layer) ---

@router.message(F.text == "Найти билеты")
async def start_search(msg: types.Message, state: FSMContext):
    await state.set_state(SimpleSearch.from_city)
    await msg.answer("🛫 Откуда вылетаем?", reply_markup=keyboards.back_to_main())

@router.message(SimpleSearch.from_city)
async def select_origin(msg: types.Message, state: FSMContext):
    if msg.text == "⬅️ Назад в меню":
        await state.clear()
        return await msg.answer("Меню", reply_markup=keyboards.main_menu())

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
    await msg.answer("Как полетим?", reply_markup=keyboards.trip_type_kb())

@router.message(SimpleSearch.trip_type)
async def select_trip_type(msg: types.Message, state: FSMContext):
    if msg.text == "В одну сторону":
        await state.update_data(trip_type="one_way")
        await state.set_state(SimpleSearch.dates)
    elif msg.text == "Туда-обратно":
        await state.update_data(trip_type="round_trip")
        await state.set_state(SimpleSearch.depart_date)
    else:
        return await msg.answer("Выберите вариант на клавиатуре.")

    now = datetime.now()
    await msg.answer("📅 Выберите дату вылета:", reply_markup=build_calendar(now.year, now.month))

# Единый обработчик навигации календаря (вместо двух огромных функций)
@router.callback_query(F.data.startswith("prev_"))
@router.callback_query(F.data.startswith("next_"))
async def calendar_navigation(callback: types.CallbackQuery, state: FSMContext):
    await update_calendar_view(callback, state)

# Обработка выбора даты
@router.callback_query(F.data.startswith("date_"))
async def date_selection(callback: types.CallbackQuery, state: FSMContext):
    _, year, month, day = callback.data.split("_")
    selected_date = f"{day.zfill(2)}.{month.zfill(2)}.{year}"
    
    current_state = await state.get_state()
    
    # 1. ONE WAY
    if current_state == SimpleSearch.dates:
        await state.update_data(dates=selected_date)
        await finish_search_one_way(callback.message, state)
    
    # 2. ROUND TRIP - Вылет
    elif current_state == SimpleSearch.depart_date:
        await state.update_data(depart_date=selected_date)
        await state.set_state(SimpleSearch.return_date)
        
        # Показываем календарь снова для обратной даты
        dt = datetime.strptime(selected_date, "%d.%m.%Y")
        await callback.message.edit_text(f"Вылет: {selected_date}.\n📅 Выберите дату возвращения:")
        await callback.message.edit_reply_markup(
            reply_markup=build_calendar(dt.year, dt.month, min_date=dt)
        )
    
    # 3. ROUND TRIP - Возврат
    elif current_state == SimpleSearch.return_date:
        await state.update_data(return_date=selected_date)
        await finish_search_round_trip(callback.message, state)
    
    await callback.answer()

# --- ФИНАЛЬНЫЕ ФУНКЦИИ (Business Logic Integration) ---

async def finish_search_one_way(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    api_date = format_date_for_api(data['dates'])
    
    await msg.answer(f"🔎 Ищу билеты {data['from_city']} → {data['to_city']} на {data['dates']}...")
    
    # Вызов API
    result = await parse_flights(
        origin=data['from_code'],
        destination=data['to_code'],
        depart_date=api_date,
        endpoint="latest"
    )
    
    if not result.get('data'):
        await msg.answer("😔 Билеты не найдены.")
        return await state.clear()

    # Фильтрация
    user_filters = await filters_repo.get_filters(msg.chat.id)
    flights = await filter_flights(result['data'], data, user_filters)
    
    if not flights:
        await msg.answer("❌ Нет билетов, подходящих под ваши фильтры.")
        return await state.clear()

    # Сортировка и Вывод (Используем utils!)
    flights.sort(key=lambda x: x.get('price', float('inf')))
    
    response = "🎫 **Найденные билеты:**\n\n"
    for i, flight in enumerate(flights[:5], 1):
        response += format_one_way_ticket(flight, data['from_city'], data['to_city'], i)
    
    await msg.answer(response, parse_mode="Markdown", disable_web_page_preview=True)
    
    # Сохраняем контекст для кнопки "Отслеживать"
    global last_search_data
    last_search_data = {**data, 'trip_type': 'one_way'}
    await offer_tracking(msg)
    await state.clear()

async def finish_search_round_trip(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    date_there = format_date_for_api(data['depart_date'])
    date_back = format_date_for_api(data['return_date'])
    
    await msg.answer("🔎 Ищу билеты туда-обратно...")
    
    # Параллельные запросы (Asyncio Gather)
    task1 = parse_flights(data['from_code'], data['to_code'], date_there)
    task2 = parse_flights(data['to_code'], data['from_code'], date_back)
    
    res_there, res_back = await asyncio.gather(task1, task2)
    
    if not res_there.get('data') or not res_back.get('data'):
        await msg.answer("❌ Не удалось найти билеты в одну из сторон.")
        return await state.clear()

    # Сортировка
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
    await msg.answer("Хотите получать уведомления, если цена изменится?", reply_markup=kb)