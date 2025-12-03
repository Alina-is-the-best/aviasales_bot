from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

import keyboards
from states import ComplexSearch
from calendar_kb import build_calendar

router = Router()


def register(dp):
    dp.include_router(router)


# ----------------------------------------------------------
# ЗАПУСК СЛОЖНОГО МАРШРУТА
# ----------------------------------------------------------
@router.message(F.text == "Сложный маршрут")
async def start_complex(msg: types.Message, state: FSMContext):
    await state.update_data(segments=[])
    await state.set_state(ComplexSearch.segment_from)

    await msg.answer(
        "Введите город вылета для первого сегмента:",
        reply_markup=keyboards.back_to_main()
    )


# ----------------------------------------------------------
# ВВОД FROM
# ----------------------------------------------------------
@router.message(ComplexSearch.segment_from)
async def segment_from(msg: types.Message, state: FSMContext):
    if msg.text == "⬅️ Назад в меню":
        await state.clear()
        return await msg.answer("Главное меню:", reply_markup=keyboards.main_menu())

    await state.update_data(segment_from=msg.text)
    await state.set_state(ComplexSearch.segment_to)

    await msg.answer(
        "Введите город прилёта:",
        reply_markup=keyboards.back_to_main()
    )


# ----------------------------------------------------------
# ВВОД TO
# ----------------------------------------------------------
@router.message(ComplexSearch.segment_to)
async def segment_to(msg: types.Message, state: FSMContext):
    if msg.text == "⬅️ Назад в меню":
        await state.clear()
        return await msg.answer("Главное меню:", reply_markup=keyboards.main_menu())

    await state.update_data(segment_to=msg.text)

    now = datetime.now()

    # Если сегмент НЕ первый → ограничить min_date
    data = await state.get_data()
    if data["segments"]:
        last_date = datetime.strptime(data["segments"][-1]["date"], "%d.%m.%Y")
        min_date = last_date + timedelta(days=1)
    else:
        min_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    await state.update_data(min_date=min_date)

    await state.set_state(ComplexSearch.segment_date)
    await msg.answer(
        "Выберите дату сегмента:",
        reply_markup=build_calendar(now.year, now.month, min_date=min_date)
    )


# ----------------------------------------------------------
# ВЫБОР ДАТЫ СЕГМЕНТА
# ----------------------------------------------------------
@router.callback_query(F.data.startswith("date_"), ComplexSearch.segment_date)
async def choose_segment_date(callback: types.CallbackQuery, state: FSMContext):
    _, y, m, d = callback.data.split("_")
    date_selected = f"{d}.{m}.{y}"

    data = await state.get_data()
    segments = data["segments"]

    segment = {
        "from": data["segment_from"],
        "to": data["segment_to"],
        "date": date_selected
    }

    segments.append(segment)

    await state.update_data(segments=segments)

    await callback.message.answer(
        f"Добавлен сегмент:\n"
        f"{segment['from']} → {segment['to']} | {segment['date']}\n\n"
        f"Хотите добавить ещё один сегмент?",
        reply_markup=keyboards.complex_add_more_kb()
    )

    await state.set_state(ComplexSearch.add_more)
    await callback.answer()


# ----------------------------------------------------------
# ЛИСТАНИЕ КАЛЕНДАРЯ ДЛЯ СЕГМЕНТОВ
# ----------------------------------------------------------
@router.callback_query(F.data.startswith("prev_"), ComplexSearch.segment_date)
async def prev_month_segment(callback: types.CallbackQuery, state: FSMContext):
    _, y, m = callback.data.split("_")
    y = int(y)
    m = int(m)

    data = await state.get_data()
    min_date = data["min_date"]

    await callback.message.edit_reply_markup(
        reply_markup=build_calendar(y, m, min_date=min_date)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("next_"), ComplexSearch.segment_date)
async def next_month_segment(callback: types.CallbackQuery, state: FSMContext):
    _, y, m = callback.data.split("_")
    y = int(y)
    m = int(m)

    data = await state.get_data()
    min_date = data["min_date"]

    await callback.message.edit_reply_markup(
        reply_markup=build_calendar(y, m, min_date=min_date)
    )
    await callback.answer()


# ----------------------------------------------------------
# ДОБАВИТЬ СЕГМЕНТ / ЗАВЕРШИТЬ
# ----------------------------------------------------------
@router.message(ComplexSearch.add_more)
async def add_more(msg: types.Message, state: FSMContext):

    # Назад
    if msg.text == "⬅️ Назад в меню":
        await state.clear()
        return await msg.answer("Главное меню:", reply_markup=keyboards.main_menu())

    # Добавить сегмент
    if msg.text == "➕ Добавить сегмент":
        await state.set_state(ComplexSearch.segment_from)
        return await msg.answer(
            "Введите город вылета следующего сегмента:",
            reply_markup=keyboards.back_to_main()
        )

    # Завершить
    if msg.text == "✔ Завершить маршрут":
        data = await state.get_data()
        segments = data["segments"]

        text = "Ваш маршрут:\n\n"
        for i, seg in enumerate(segments, 1):
            text += f"{i}. {seg['from']} → {seg['to']} | {seg['date']}\n"

        await msg.answer(text)

        await state.set_state(ComplexSearch.baggage)
        return await msg.answer(
            "Нужен багаж?",
            reply_markup=keyboards.baggage_kb()
        )

    await msg.answer("Выберите действие с кнопок.")


# ----------------------------------------------------------
# БАГАЖ
# ----------------------------------------------------------
@router.message(ComplexSearch.baggage)
async def complex_baggage(msg: types.Message, state: FSMContext):

    if msg.text == "⬅️ Назад в меню":
        await state.clear()
        return await msg.answer("Главное меню:", reply_markup=keyboards.main_menu())

    await state.update_data(baggage=msg.text)

    await state.set_state(ComplexSearch.transfers)
    await msg.answer(
        "Пересадки?",
        reply_markup=keyboards.transfers_kb()
    )


# ----------------------------------------------------------
# ПЕРЕСАДКИ
# ----------------------------------------------------------
@router.message(ComplexSearch.transfers)
async def complex_transfers(msg: types.Message, state: FSMContext):

    if msg.text == "⬅️ Назад в меню":
        await state.clear()
        return await msg.answer("Главное меню:", reply_markup=keyboards.main_menu())

    await state.update_data(transfers=msg.text)

    await state.set_state(ComplexSearch.price_limit)
    await msg.answer(
        "Введите лимит цены:",
        reply_markup=keyboards.back_to_main()
    )


# ----------------------------------------------------------
# ФИНАЛ — ЦЕНА
# ----------------------------------------------------------
@router.message(ComplexSearch.price_limit)
async def complex_price(msg: types.Message, state: FSMContext):

    if msg.text == "⬅️ Назад в меню":
        await state.clear()
        return await msg.answer("Главное меню:", reply_markup=keyboards.main_menu())

    await state.update_data(price_limit=msg.text)
    data = await state.get_data()

    segments = data["segments"]

    text = "Ваш сложный маршрут ✈️:\n\n"
    for i, seg in enumerate(segments, 1):
        text += f"{i}. {seg['from']} → {seg['to']} | {seg['date']}\n"

    text += (
        f"\nБагаж: {data['baggage']}\n"
        f"Пересадки: {data['transfers']}\n"
        f"Цена: до {data['price_limit']}₽"
    )

    await msg.answer(text, reply_markup=keyboards.main_menu())

    await state.clear()
