from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from datetime import datetime

import keyboards
from states import SimpleSearch
from calendar_kb import build_calendar
import filters_repository as filters_repo

router = Router()


def register(dp):
    dp.include_router(router)


# ------------------------------------------------
# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ФИНАЛЬНОГО ШАГА
# ------------------------------------------------
async def finish_search(msg: types.Message, state: FSMContext):
    data = await state.get_data()

    # текст даты
    if data.get("dates"):
        date_text = data["dates"]
    else:
        date_text = f"Туда: {data['depart_date']}, Обратно: {data['return_date']}"

    await msg.answer(
        "Запрос собран ✈️\n\n"
        f"Откуда: {data['from_city']}\n"
        f"Куда: {data['to_city']}\n"
        f"Тип маршрута: {data['trip_type']}\n"
        f"Дата: {date_text}\n"
        f"Багаж: {data['baggage']}\n"
        f"Пересадки: {data['transfers']}\n"
        f"Цена: до {data['price_limit']}₽\n\n"
        "Скоро подключим поиск билетов.",
        reply_markup=keyboards.main_menu()
    )

    await state.clear()


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
    await state.update_data(from_city=msg.text)
    await state.set_state(SimpleSearch.to_city)
    await msg.answer("Введите город прилёта:", reply_markup=keyboards.back_to_main())


# 2. КУДА
@router.message(SimpleSearch.to_city)
async def simple_to(msg: types.Message, state: FSMContext):
    await state.update_data(to_city=msg.text)
    await state.set_state(SimpleSearch.trip_type)
    await msg.answer(
        "Выберите тип маршрута:",
        reply_markup=keyboards.trip_type_kb()
    )


# 3. ONE-WAY или ROUND-TRIP
@router.message(SimpleSearch.trip_type)
async def simple_trip_type(msg: types.Message, state: FSMContext):

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
        return await finish_search(msg, state)

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
    await state.update_data(baggage=msg.text)
    await msg.answer(
        "Тип пересадок:",
        reply_markup=keyboards.transfers_kb()
    )
    await state.set_state(SimpleSearch.transfers)


# ------------------------------------------------
# ПЕРЕСАДКИ
# ------------------------------------------------
@router.message(SimpleSearch.transfers)
async def transfers_step(msg: types.Message, state: FSMContext):
    await state.update_data(transfers=msg.text)

    filters = await filters_repo.get_filters(msg.from_user.id)

    if filters.price_limit:
        await state.update_data(price_limit=filters.price_limit)
        await msg.answer(f"Цена: до {filters.price_limit}₽ (по фильтру)")
        return await finish_search(msg, state)

    await state.set_state(SimpleSearch.price_limit)
    await msg.answer("Введите ограничение по цене:", reply_markup=keyboards.back_to_main())


# ------------------------------------------------
# ЦЕНА — ФИНАЛ
# ------------------------------------------------
@router.message(SimpleSearch.price_limit)
async def price_step(msg: types.Message, state: FSMContext):
    await state.update_data(price_limit=msg.text)
    await finish_search(msg, state)
