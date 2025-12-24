from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, timedelta

from infra.keyboards import keyboards
from infra.states import ComplexSearch
from infra.keyboards.calendar_kb import build_calendar


router = Router()

def register(dp):
    dp.include_router(router)

# --- ХЕНДЛЕР ДЛЯ КНОПКИ "НАЗАД В МЕНЮ" ---
@router.message(F.text == "⬅️ Назад в меню", ComplexSearch.segment_from)
@router.message(F.text == "⬅️ Назад в меню", ComplexSearch.segment_to)
@router.message(F.text == "⬅️ Назад в меню", ComplexSearch.segment_date)
@router.message(F.text == "⬅️ Назад в меню", ComplexSearch.add_more)
@router.message(F.text == "⬅️ Назад в меню", ComplexSearch.baggage)
@router.message(F.text == "⬅️ Назад в меню", ComplexSearch.transfers)
@router.message(F.text == "⬅️ Назад в меню", ComplexSearch.price_limit)
async def back_to_menu_from_complex(msg: types.Message, state: FSMContext):
    """Обработка кнопки 'Назад в меню' во время сложного поиска"""
    await state.clear()
    await msg.answer(
        "Главное меню:",
        reply_markup=keyboards.main_menu()
    )

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
async def _calc_min_date_for_segment(state: FSMContext) -> datetime:
    data = await state.get_data()
    segments = data.get("segments", [])
    if segments:
        try:
            last_date = datetime.strptime(segments[-1]["date"], "%d.%m.%Y")
            return last_date + timedelta(days=1)
        except: 
            pass
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

# --- ОСНОВНЫЕ ХЕНДЛЕРЫ ---

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

# --- ОБРАБОТКА КАЛЕНДАРЯ ---

@router.callback_query(F.data.startswith(("prev_", "next_")))
async def calendar_navigation(callback: types.CallbackQuery, state: FSMContext):
    """Обработка листания месяцев в календаре"""
    # Проверяем, находимся ли мы в состоянии, где нужен календарь
    current_state = await state.get_state()
    
    if current_state == ComplexSearch.segment_date.state:
        data = await state.get_data()
        min_date = data.get("min_date")
        
        # Получаем данные из callback
        action, year, month = callback.data.split("_")
        year, month = int(year), int(month)
        
        # Обновляем календарь
        await callback.message.edit_reply_markup(
            reply_markup=build_calendar(year, month, min_date=min_date)
        )
    await callback.answer()

@router.callback_query(F.data.startswith("date_"))
async def handle_date_selection(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора даты"""
    current_state = await state.get_state()
    
    # Для выбора даты сегмента сложного маршрута
    if current_state == ComplexSearch.segment_date.state:
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

# --- ДАЛЬНЕЙШИЕ ШАГИ (НУЖНО ДОПИСАТЬ) ---

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

# --- ФУНКЦИЯ ПОИСКА ДЛЯ СЛОЖНОГО МАРШРУТА ---
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
