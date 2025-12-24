from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

from infra.keyboards import keyboards
from infra.states import ComplexSearch
from infra.keyboards.calendar_kb import build_calendar

from adapters.api.aviasales_api import parse_flights
from models.data.city_codes import get_city_code

router = Router()


def register(dp):
    dp.include_router(router)


# получаем min_date для даты сегмента
async def _calc_min_date_for_segment(state: FSMContext) -> datetime:
    data = await state.get_data()
    segments = data.get("segments", [])

    # если сегменты уже есть — следующий сегмент не раньше (последняя дата + 1 день)
    if segments:
        last_date = datetime.strptime(segments[-1]["date"], "%d.%m.%Y")
        return last_date + timedelta(days=1)

    # иначе: не раньше сегодня
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


# ЗАПУСК СЛОЖНОГО МАРШРУТА
@router.message(F.text == "Сложный маршрут")
async def start_complex(msg: types.Message, state: FSMContext):
    await state.update_data(segments=[])
    await state.set_state(ComplexSearch.segment_from)

    await msg.answer(
        "Введите город вылета для первого сегмента:",
        reply_markup=keyboards.back_to_main()
    )


# FROM
@router.message(ComplexSearch.segment_from)
async def segment_from(msg: types.Message, state: FSMContext):
    await state.update_data(segment_from=msg.text)
    await state.set_state(ComplexSearch.segment_to)

    await msg.answer(
        "Введите город прилёта:",
        reply_markup=keyboards.back_to_main()
    )


# TO
@router.message(ComplexSearch.segment_to)
async def segment_to(msg: types.Message, state: FSMContext):
    await state.update_data(segment_to=msg.text)

    now = datetime.now()
    min_date = await _calc_min_date_for_segment(state)
    await state.update_data(min_date=min_date)

    await state.set_state(ComplexSearch.segment_date)
    await msg.answer(
        "Выберите дату сегмента:",
        reply_markup=build_calendar(now.year, now.month, min_date=min_date)
    )


# ВЫБОР ДАТЫ СЕГМЕНТА
@router.callback_query(F.data.startswith("date_"), ComplexSearch.segment_date)
async def choose_segment_date(callback: types.CallbackQuery, state: FSMContext):
    _, y, m, d = callback.data.split("_")
    date_selected = f"{d}.{m}.{y}"

    data = await state.get_data()
    segments = data.get("segments", [])

    segment = {
        "from": data["segment_from"],
        "to": data["segment_to"],
        "date": date_selected
    }

    segments.append(segment)
    await state.update_data(segments=segments)

    await callback.message.answer(
        "Добавлен сегмент:\n"
        f"{segment['from']} → {segment['to']} | {segment['date']}\n\n"
        "Хотите добавить ещё один сегмент?",
        reply_markup=keyboards.complex_add_more_kb()
    )

    await state.set_state(ComplexSearch.add_more)
    await callback.answer()


# ЛИСТАНИЕ КАЛЕНДАРЯ ДЛЯ СЕГМЕНТОВ (DRY: один обработчик)
@router.callback_query(F.data.startswith(("prev_", "next_")), ComplexSearch.segment_date)
async def change_month_segment(callback: types.CallbackQuery, state: FSMContext):
    _, y, m = callback.data.split("_")
    y, m = int(y), int(m)

    data = await state.get_data()
    min_date = data.get("min_date")

    await callback.message.edit_reply_markup(
        reply_markup=build_calendar(y, m, min_date=min_date)
    )
    await callback.answer()


# ДОБАВИТЬ СЕГМЕНТ / ЗАВЕРШИТЬ
@router.message(ComplexSearch.add_more)
async def add_more(msg: types.Message, state: FSMContext):
    if msg.text == "➕ Добавить сегмент":
        await state.set_state(ComplexSearch.segment_from)
        return await msg.answer(
            "Введите город вылета следующего сегмента:",
            reply_markup=keyboards.back_to_main()
        )

    if msg.text == "✔ Завершить маршрут":
        data = await state.get_data()
        segments = data.get("segments", [])

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


# БАГАЖ
@router.message(ComplexSearch.baggage)
async def complex_baggage(msg: types.Message, state: FSMContext):
    await state.update_data(baggage=msg.text)

    await state.set_state(ComplexSearch.transfers)
    await msg.answer(
        "Пересадки?",
        reply_markup=keyboards.transfers_kb()
    )


# ПЕРЕСАДКИ
@router.message(ComplexSearch.transfers)
async def complex_transfers(msg: types.Message, state: FSMContext):
    await state.update_data(transfers=msg.text)

    await state.set_state(ComplexSearch.price_limit)
    await msg.answer(
        "Введите лимит цены:",
        reply_markup=keyboards.back_to_main()
    )


# ЦЕНА
@router.message(ComplexSearch.price_limit)
async def complex_price(msg: types.Message, state: FSMContext):
    await state.update_data(price_limit=msg.text)
    data = await state.get_data()

    segments = data.get("segments", [])

    # Формируем текст маршрута
    text = "Ищу билеты по вашему маршруту:\n\n"
    for i, seg in enumerate(segments, 1):
        text += f"{i}. {seg['from']} → {seg['to']} | {seg['date']}\n"

    text += (
        f"\nБагаж: {data.get('baggage', '')}\n"
        f"Пересадки: {data.get('transfers', '')}\n"
        f"Цена: до {data.get('price_limit', '')}₽"
    )

    await msg.answer(text, reply_markup=keyboards.main_menu())

    # Пример: ищем билеты для первого сегмента
    if segments:
        first_segment = segments[0]
        try:
            from_code = get_city_code(first_segment["from"])
            to_code = get_city_code(first_segment["to"])

            result = await parse_flights(
                origin=from_code,
                destination=to_code,
                depart_date=first_segment["date"],
                currency="RUB",
                endpoint="latest"
            )

            if not result.get("error") and result.get("data"):
                flights = result["data"]

                # фильтр по цене
                price_limit_str = data.get("price_limit", "")
                if price_limit_str.isdigit():
                    limit = int(price_limit_str)
                    flights = {
                        k: v for k, v in flights.items()
                        if isinstance(v, dict) and v.get("value", float("inf")) <= limit
                    }

                if flights:
                    flight_text = (
                        f"Найденные билеты для {first_segment['from']} → {first_segment['to']}:\n\n"
                    )
                    for _, flight in list(flights.items())[:3]:
                        flight_text += (
                            f"• Цена: {flight.get('value', '?')}₽\n"
                            f"  Авиакомпания: {flight.get('airline', 'Неизвестно')}\n"
                            f"  Пересадки: {flight.get('transfers', '0')}\n\n"
                        )
                    await msg.answer(flight_text)
                else:
                    await msg.answer("Билеты не найдены или не соответствуют фильтрам.")

        except Exception as e:
            await msg.answer(f"Ошибка при поиске: {str(e)}")

    await state.clear()
