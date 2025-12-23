from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import keyboards
from states import SimpleSearch
from calendar_kb import build_calendar
import filters_repository as filters_repo
from parser.aviasales_api import parse_flights
from city_codes import get_city_code
from datetime import datetime, timedelta

router = Router()


def register(dp):
    dp.include_router(router)

# Глобальное хранилище последнего поиска (для кнопки добавления)
last_search_data = {}

# Добавьте эту функцию после импортов, но перед основной логикой
async def debug_api_response(result):
    """Функция для отладки ответа API"""
    print("=== DEBUG API RESPONSE ===")
    print(f"Has error: {result.get('error')}")
    print(f"Has data: {bool(result.get('data'))}")
    
    if result.get('data'):
        data = result['data']
        print(f"Data type: {type(data)}")
        print(f"Data keys: {list(data.keys())[:5] if isinstance(data, dict) else 'Not a dict'}")
        
        if isinstance(data, dict):
            # Посмотрим на первый элемент
            for key, value in list(data.items())[:1]:
                print(f"First item key: {key}")
                print(f"First item value type: {type(value)}")
                if isinstance(value, dict):
                    print(f"First item value keys: {list(value.keys())}")
    print("=== END DEBUG ===")

# --------------------------------------------------------------
# Применение фильтров к результатам API
# --------------------------------------------------------------
async def apply_filters_to_flights(flights_data, filters, user_filters):
    """Применяет фильтры к найденным рейсам (обновленная для v3 API)"""
    
    # Проверяем тип данных
    print(f"=== APPLY FILTERS DEBUG ===")
    print(f"flights_data type: {type(flights_data)}")
    
    # Обработка разных форматов API
    
    # 1. Если это список (новый v3 API формат)
    if isinstance(flights_data, list):
        print(f"Processing V3 API format (list with {len(flights_data)} items)")
        filtered_flights = []
        
        for flight in flights_data:
            if not isinstance(flight, dict):
                continue
            
            # Проверяем фильтры
            skip = False
            
            # Фильтр по цене (постоянные фильтры пользователя)
            if user_filters.price_limit and user_filters.price_limit.isdigit():
                price_limit = int(user_filters.price_limit)
                flight_price = flight.get('value', flight.get('price', float('inf')))
                if flight_price > price_limit:
                    skip = True
            
            # Фильтр по цене (фильтры текущего поиска)
            if not skip and filters.get('price_limit') and str(filters.get('price_limit')).isdigit():
                price_limit = int(filters.get('price_limit'))
                flight_price = flight.get('value', flight.get('price', float('inf')))
                if flight_price > price_limit:
                    skip = True
            
            # Фильтр по пересадкам
            # В endpoint "dates" поле называется number_of_changes
            # В endpoint "latest" поле называется transfers
            transfers = flight.get('number_of_changes', flight.get('transfers', 0))
            
            # Проверяем постоянный фильтр пересадок
            if user_filters.transfers == "Только прямой рейс" and transfers > 0:
                skip = True
                
            # Проверяем фильтр текущего поиска
            if not skip and filters.get('transfers') == "Только прямой" and transfers > 0:
                skip = True
            
            if not skip:
                filtered_flights.append(flight)
        
        print(f"After filtering: {len(filtered_flights)} flights")
        return filtered_flights
    
    # 2. Если это словарь (старый v1 API формат)
    elif isinstance(flights_data, dict):
        print(f"Processing V1 API format (dict)")
        filtered_flights = []
        
        for destination, flights_dict in flights_data.items():
            if not isinstance(flights_dict, dict):
                continue
            
            for flight_key, flight in flights_dict.items():
                if not isinstance(flight, dict):
                    continue
                
                # Проверяем фильтры (старая логика)
                skip = False
                
                # Фильтр по цене (постоянные фильтры пользователя)
                if user_filters.price_limit and user_filters.price_limit.isdigit():
                    price_limit = int(user_filters.price_limit)
                    flight_price = flight.get('price', float('inf'))
                    if flight_price > price_limit:
                        skip = True
                
                # Фильтр по цене (фильтры текущего поиска)
                if not skip and filters.get('price_limit') and str(filters.get('price_limit')).isdigit():
                    price_limit = int(filters.get('price_limit'))
                    flight_price = flight.get('price', float('inf'))
                    if flight_price > price_limit:
                        skip = True
                
                # Фильтр по пересадкам (в старом API может быть поле 'transfers')
                transfers = flight.get('transfers', 0)
                
                if user_filters.transfers == "Только прямой рейс" and transfers > 0:
                    skip = True
                    
                if not skip and filters.get('transfers') == "Только прямой" and transfers > 0:
                    skip = True
                
                if not skip:
                    flight['destination_code'] = destination
                    filtered_flights.append(flight)
        
        print(f"After filtering: {len(filtered_flights)} flights")
        return filtered_flights
    
    # 3. Если это другой формат (например, словарь с ключом 'data')
    elif isinstance(flights_data, dict) and 'data' in flights_data:
        print(f"Processing dict with 'data' key")
        # Рекурсивно вызываем для содержимого 'data'
        return await apply_filters_to_flights(flights_data['data'], filters, user_filters)
    
    # 4. Неизвестный формат
    else:
        print(f"Unknown flights_data format: {type(flights_data)}")
        return []


# --------------------------------------------------------------
# Финальный шаг поиска туда с парсингом
# --------------------------------------------------------------

async def finish_search_one_way(msg: types.Message, state: FSMContext):
    """Завершает поиск для маршрута 'В одну сторону'"""
    data = await state.get_data()
    
    # Отладочный вывод
    print(f"=== ONE-WAY DEBUG ===")
    print(f"Data keys: {list(data.keys())}")
    print(f"dates: {data.get('dates')}")
    
    # Сохраняем данные для кнопки
    global last_search_data
    last_search_data = data.copy()
    last_search_data['trip_type'] = 'one_way'
    
    # Получаем постоянные фильтры пользователя
    user_filters = await filters_repo.get_filters(msg.from_user.id)
    
    # Получаем коды городов
    from_city_code = get_city_code(data['from_city'])
    to_city_code = get_city_code(data['to_city'])
    
    # Получаем дату вылета
    depart_date = data.get("dates")
    if not depart_date:
        await msg.answer("❌ Ошибка: не найдена дата вылета.")
        await state.clear()
        return
    
    # Форматируем дату для API
    try:
        day, month, year = depart_date.split('.')
        # Добавляем ведущие нули: "2" → "02", "1" → "01"
        api_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        last_search_data['api_date'] = api_date
        print(f"Форматированная дата для API: {api_date}")
    except Exception as e:
        await msg.answer(f"❌ Ошибка формата даты: {depart_date}")
        print(f"Ошибка форматирования даты: {e}")
        await state.clear()
        return
    
    # Для one-way используем endpoint "latest" (v3 API)
    endpoint = "latest"
    
    await msg.answer(f"🔍 Ищу билеты {data['from_city']} → {data['to_city']} на {depart_date}...")
    
    try:
        # Вызываем API для one-way (v3 API)
        result = await parse_flights(
            origin=from_city_code,
            destination=to_city_code,
            depart_date=api_date,
            currency="RUB",
            endpoint=endpoint
        )
        
        print(f"=== API RESULT FOR {endpoint} ===")
        print(f"Has error: {result.get('error')}")
        
        if result.get("error"):
            await msg.answer(f"❌ Ошибка API: {result['error']}")
            await state.clear()
            return
            
        # Получаем данные о рейсах
        raw_flights = result.get("data", {})
        
        print(f"=== PROCESSING API DATA ===")
        print(f"raw_flights type: {type(raw_flights)}")
        if isinstance(raw_flights, dict):
            print(f"raw_flights keys: {list(raw_flights.keys())}")
        
        if not raw_flights:
            await msg.answer("❌ Билеты по вашему запросу не найдены в API.")
            await state.clear()
            return
        
        # Применяем фильтры (возможно, нужно обновить эту функцию для v3 API)
        filtered_flights = await apply_filters_to_flights(raw_flights, data, user_filters)
        
        # Применяем фильтры
        filtered_flights = await apply_filters_to_flights(raw_flights, data, user_filters)

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
    )


# ------------------------------------------------
# ПРОСТОЙ МАРШРУТ — ШАГИ
# ------------------------------------------------

# 1. ОТКУДА
@router.message(F.text == "Простой маршрут")
async def simple_start(msg: types.Message, state: FSMContext):

    filters = await filters_repo.get_filters(msg.from_user.id)

    # если есть постоянный фильтр — пропускаем вопрос
    if filters.from_city:
        await state.update_data(from_city=filters.from_city)
        await state.set_state(SimpleSearch.to_city)
        return await msg.answer(
            f"Город вылета установлен по фильтру: {filters.from_city}\nВведите город прилёта:",
            reply_markup=keyboards.back_to_main()
        )

    # иначе спрашиваем пользователя
    await state.set_state(SimpleSearch.from_city)
    await msg.answer("Введите город вылета:", reply_markup=keyboards.back_to_main())


@router.message(SimpleSearch.from_city)
async def simple_from(msg: types.Message, state: FSMContext):
    if msg.text == "⬅️ Назад в меню":
        await state.clear()
        return await msg.answer("Главное меню:", reply_markup=keyboards.main_menu())

    await state.update_data(from_city=msg.text)
    await state.set_state(SimpleSearch.to_city)
    await msg.answer("Введите город прилёта:", reply_markup=keyboards.back_to_main())


# 2. КУДА
@router.message(SimpleSearch.to_city)
async def simple_to(msg: types.Message, state: FSMContext):
    if msg.text == "⬅️ Назад в меню":
        await state.clear()
        return await msg.answer("Главное меню:", reply_markup=keyboards.main_menu())

    await state.update_data(to_city=msg.text)
    await state.set_state(SimpleSearch.trip_type)
    await msg.answer(
        "Выберите тип маршрута:",
        reply_markup=keyboards.trip_type_kb()
    )


# 3. ONE-WAY или ROUND-TRIP
@router.message(SimpleSearch.trip_type)
async def simple_trip_type(msg: types.Message, state: FSMContext):
    if msg.text == "⬅️ Назад в меню":
        await state.clear()
        return await msg.answer("Главное меню:", reply_markup=keyboards.main_menu())

    trip = msg.text.lower()
    if trip not in ["в одну сторону", "туда-обратно"]:
        return await msg.answer("Выберите вариант из кнопок.")

    await state.update_data(trip_type=trip)

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    now = datetime.now()

    # One Way
    if trip == "в одну сторону":
        await state.set_state(SimpleSearch.dates)
        return await msg.answer(
            "Выберите дату вылета:",
            reply_markup=build_calendar(now.year, now.month, min_date=today)
        )

    # Round Trip
    await state.set_state(SimpleSearch.depart_date)
    await msg.answer(
        "Выберите дату вылета:",
        reply_markup=build_calendar(now.year, now.month, min_date=today)
    )


# ------------------------------------------------
# ONE-WAY ДАТА
# ------------------------------------------------
@router.callback_query(F.data.startswith("date_"), SimpleSearch.dates)
async def choose_oneway_date(callback: types.CallbackQuery, state: FSMContext):

    _, y, m, d = callback.data.split("_")
    date_str = f"{d}.{m}.{y}"

    await state.update_data(dates=date_str)

    # проверяем фильтры
    filters = await filters_repo.get_filters(callback.from_user.id)

    # если есть фильтр багаж — пропускаем вопрос
    if filters.baggage:
        await state.update_data(baggage=filters.baggage)
        await callback.message.answer(f"Багаж: {filters.baggage} (по фильтру)")
        await state.set_state(SimpleSearch.transfers)

        # если есть фильтр пересадок — пропускаем
        if filters.transfers:
            await state.update_data(transfers=filters.transfers)
            await callback.message.answer(f"Пересадки: {filters.transfers} (по фильтру)")
            return await ask_price_or_skip(callback.message, state, filters)

        return await callback.message.answer(
            "Тип пересадок:",
            reply_markup=keyboards.transfers_kb()
        )

    # иначе задаём вопрос
    await state.set_state(SimpleSearch.baggage)
    await callback.message.answer(
        f"Дата выбрана: {date_str}\nВыберите багаж:",
        reply_markup=keyboards.baggage_kb()
    )
    await callback.answer()


# ------------------------------------------------
# ROUND TRIP: ДАТА ВЫЛЕТА
# ------------------------------------------------
@router.callback_query(F.data.startswith("date_"), SimpleSearch.depart_date)
async def choose_depart_date(callback: types.CallbackQuery, state: FSMContext):

    _, y, m, d = callback.data.split("_")
    depart = f"{d}.{m}.{y}"

    await state.update_data(depart_date=depart)

    now = datetime.now()
    min_date = datetime.strptime(depart, "%d.%m.%Y")

    await state.set_state(SimpleSearch.return_date)
    await callback.message.answer(
        f"Дата вылета выбрана: {depart}\nТеперь выберите дату возвращения:",
        reply_markup=build_calendar(now.year, now.month, min_date=min_date)
    )
    await callback.answer()


# ------------------------------------------------
# ROUND TRIP: ДАТА ВОЗВРАЩЕНИЯ
# ------------------------------------------------
@router.callback_query(F.data.startswith("date_"), SimpleSearch.return_date)
async def choose_return_date(callback: types.CallbackQuery, state: FSMContext):

    _, y, m, d = callback.data.split("_")
    return_date = f"{d}.{m}.{y}"

    data = await state.get_data()
    depart = data["depart_date"]

    await state.update_data(return_date=return_date)

    await callback.message.answer(
        f"Маршрут выбран:\nТуда: {depart}\nОбратно: {return_date}"
    )

    filters = await filters_repo.get_filters(callback.from_user.id)

    # BAGGAGE FILTER?
    if filters.baggage:
        await state.update_data(baggage=filters.baggage)
        await callback.message.answer(f"Багаж: {filters.baggage} (по фильтру)")

        # TRANSFERS FILTER?
        if filters.transfers:
            await state.update_data(transfers=filters.transfers)
            await callback.message.answer(f"Пересадки: {filters.transfers} (по фильтру)")
            return await ask_price_or_skip(callback.message, state, filters)

        await state.set_state(SimpleSearch.transfers)
        return await callback.message.answer(
            "Тип пересадок:",
            reply_markup=keyboards.transfers_kb()
        )

    # иначе задаём вопрос
    await state.set_state(SimpleSearch.baggage)
    await callback.message.answer(
        "Выберите багаж:",
        reply_markup=keyboards.baggage_kb()
    )
    await callback.answer()


# ------------------------------------------------
# ФУНКЦИЯ ПРОВЕРКИ ЦЕНОВОГО ФИЛЬТРА
# ------------------------------------------------
async def ask_price_or_skip(msg: types.Message, state: FSMContext, filters):
    if filters.price_limit:
        await state.update_data(price_limit=filters.price_limit)
        await msg.answer(f"Цена: до {filters.price_limit}₽ (по фильтру)")
        
        # Определяем тип маршрута и вызываем соответствующую функцию
        data = await state.get_data()
        trip_type = data.get('trip_type', '').lower()
        
        if 'в одну сторону' in trip_type:
            return await finish_search_one_way(msg, state)
        else:
            return await finish_search_round_trip(msg, state)

    await state.set_state(SimpleSearch.price_limit)
    return await msg.answer(
        "Введите ограничение по цене:",
        reply_markup=keyboards.back_to_main()
    )

# ------------------------------------------------
# БАГАЖ
# ------------------------------------------------
@router.message(SimpleSearch.baggage)
async def baggage_step(msg: types.Message, state: FSMContext):
    if msg.text == "⬅️ Назад в меню":
        await state.clear()
        return await msg.answer(
            "Главное меню:",
            reply_markup=keyboards.main_menu()
        )
    
    await state.update_data(baggage=msg.text)
    
    # Показываем клавиатуру для выбора пересадок
    await msg.answer(
        "Тип пересадок:",
        reply_markup=keyboards.transfers_kb()  # ← ВАЖНО: должна быть эта строка!
    )
    await state.set_state(SimpleSearch.transfers)
 

# ------------------------------------------------
# ПЕРЕСАДКИ
# ------------------------------------------------
@router.message(SimpleSearch.transfers)
async def transfers_step(msg: types.Message, state: FSMContext):
    print(f"=== DEBUG transfers_step ===")
    print(f"Message text: {msg.text}")
    print(f"Current state: {await state.get_state()}")
    print(f"User ID: {msg.from_user.id}")
    
    if msg.text == "⬅️ Назад в меню":
        print("Нажата кнопка 'Назад'")
        await state.clear()
        return await msg.answer(
            "Главное меню:",
            reply_markup=keyboards.main_menu()
        )
    
    print(f"Выбран тип пересадок: {msg.text}")
    await state.update_data(transfers=msg.text)
    
    # Проверяем фильтры пользователя
    filters = await filters_repo.get_filters(msg.from_user.id)
    print(f"User filters price_limit: {filters.price_limit}")
    
    if filters.price_limit:
        print(f"Используем фильтр по цене: {filters.price_limit}")
        await state.update_data(price_limit=filters.price_limit)
        await msg.answer(f"Цена: до {filters.price_limit}₽ (по фильтру)")
        
        data = await state.get_data()
        print(f"Data keys: {list(data.keys())}")
        
        if 'dates' in data:
            print("Определен маршрут 'В одну сторону'")
            await finish_search_one_way(msg, state)
        elif 'depart_date' in data and 'return_date' in data:
            print("Определен маршрут 'Туда-обратно'")
            await finish_search_round_trip(msg, state)
        else:
            print("Не удалось определить тип маршрута")
            await msg.answer("❌ Ошибка: не удалось определить тип маршрута.")
            await state.clear()
        return
    
    print("Запрашиваем ограничение по цене у пользователя")
    await state.set_state(SimpleSearch.price_limit)
    await msg.answer(
        "Введите ограничение по цене:",
        reply_markup=keyboards.back_to_main()
    )
    print("=== END DEBUG ===")

# ------------------------------------------------
# ЦЕНА — ФИНАЛ
# ------------------------------------------------
@router.message(SimpleSearch.price_limit)
async def price_step(msg: types.Message, state: FSMContext):
    await state.update_data(price_limit=msg.text)
    
    # Определяем тип маршрута и вызываем соответствующую функцию
    data = await state.get_data()
    trip_type = data.get('trip_type', '').lower()
    
    if 'в одну сторону' in trip_type:
        await finish_search_one_way(msg, state)
    else:
        await finish_search_round_trip(msg, state)

# ------------------------------------------------
# ГЛОБАЛЬНЫЙ НАЗАД ДЛЯ ВСЕХ СОСТОЯНИЙ ПОИСКА
# ------------------------------------------------

@router.message(F.text == "⬅️ Назад в меню", SimpleSearch.from_city)
@router.message(F.text == "⬅️ Назад в меню", SimpleSearch.to_city)
@router.message(F.text == "⬅️ Назад в меню", SimpleSearch.trip_type)
@router.message(F.text == "⬅️ Назад в меню", SimpleSearch.dates)
@router.message(F.text == "⬅️ Назад в меню", SimpleSearch.depart_date)
@router.message(F.text == "⬅️ Назад в меню", SimpleSearch.return_date)
@router.message(F.text == "⬅️ Назад в меню", SimpleSearch.baggage)
@router.message(F.text == "⬅️ Назад в меню", SimpleSearch.transfers)
@router.message(F.text == "⬅️ Назад в меню", SimpleSearch.price_limit)
async def search_back(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer("Главное меню:", reply_markup=keyboards.main_menu())

# ------------------------------------------------
# ПЕРЕЛИСТЫВАНИЕ КАЛЕНДАРЯ
# ------------------------------------------------

@router.callback_query(
    F.data.startswith("prev_"),
    SimpleSearch.dates
)
@router.callback_query(
    F.data.startswith("prev_"),
    SimpleSearch.depart_date
)
@router.callback_query(
    F.data.startswith("prev_"),
    SimpleSearch.return_date
)
async def prev_month(callback: types.CallbackQuery, state: FSMContext):

    _, y, m = callback.data.split("_")
    y = int(y)
    m = int(m)

    data = await state.get_data()

    # минимальная дата может быть None
    min_date = None
    if "depart_date" in data:
        try:
            min_date = datetime.strptime(data["depart_date"], "%d.%m.%Y")
        except:
            min_date = None

    await callback.message.edit_reply_markup(
        reply_markup=build_calendar(y, m, min_date=min_date)
    )
    await callback.answer()


@router.callback_query(
    F.data.startswith("next_"),
    SimpleSearch.dates
)
@router.callback_query(
    F.data.startswith("next_"),
    SimpleSearch.depart_date
)
@router.callback_query(
    F.data.startswith("next_"),
    SimpleSearch.return_date
)
async def next_month(callback: types.CallbackQuery, state: FSMContext):

    _, y, m = callback.data.split("_")
    y = int(y)
    m = int(m)

    data = await state.get_data()

    # минимальная дата может быть None
    min_date = None
    if "depart_date" in data:
        try:
            min_date = datetime.strptime(data["depart_date"], "%d.%m.%Y")
        except:
            min_date = None

    await callback.message.edit_reply_markup(
        reply_markup=build_calendar(y, m, min_date=min_date)
    )
    await callback.answer()