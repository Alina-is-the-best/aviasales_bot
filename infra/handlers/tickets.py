from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from infra.keyboards import keyboards
from infra.states import TicketAdd
from models.repo import tickets_repository as repo

router = Router()


def register(dp):
    dp.include_router(router)


# ГЛАВНОЕ МЕНЮ РАЗДЕЛА "Мои билеты"
@router.message(F.text == "Мои билеты")
async def my_tickets_root(msg: types.Message):
    await msg.answer(
        "Выберите категорию:",
        reply_markup=keyboards.tickets_main_kb()
    )


# КУПЛЕННЫЕ БИЛЕТЫ
@router.message(F.text == "Купленные билеты")
async def purchased_tickets(msg: types.Message):
    tickets = await repo.get_tickets(msg.from_user.id)

    if not tickets:
        await msg.answer(
            "У вас пока нет купленных билетов.",
        )

        # Кнопка "Добавить билет"
        await msg.answer(
            "Добавьте первый билет:",
            reply_markup=keyboards.add_ticket_button()
        )

        return

    # формируем список
    text = "Ваши билеты:\n\n"
    for i, t in enumerate(tickets, 1):
        text += (
            f"{i}. {t.from_city} – {t.to_city}\n"
            f"{t.date}\n\n"
        )

    # кнопки
    await msg.answer(
        text,
        reply_markup=keyboards.add_ticket_button()
    )

    await msg.answer(
        "Выберите билет:",
        reply_markup=keyboards.tickets_numbers_kb(len(tickets))
    )


# ДОБАВИТЬ БИЛЕТ
@router.callback_query(F.data == "ticket_add")
async def add_ticket_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TicketAdd.waiting_for_data)

    await callback.message.answer(
        "Отправьте данные билета в формате:\n"
        "`город вылета, город прибытия, дата`\n\n"
        "Пример: `Москва, Сочи, 12.03.2025`",
        parse_mode="Markdown"
    )
    await callback.answer()


# ДОБАВЛЕНИЕ БИЛЕТА — FSM
@router.message(TicketAdd.waiting_for_data)
async def add_ticket_process(msg: types.Message, state: FSMContext):
    # Остальная логика
    parts = msg.text.split(",")

    if len(parts) != 3:
        return await msg.answer(
            "Неверный формат! Нужно три слова через запятую.\n"
            "Например: `Москва, Сочи, 12.03.2025`",
            parse_mode="Markdown"
        )

    from_city = parts[0].strip()
    to_city = parts[1].strip()
    date = parts[2].strip()

    await repo.add_ticket(msg.from_user.id, from_city, to_city, date)

    await state.clear()

    await msg.answer(
        "Билет успешно добавлен! 🎉",
        reply_markup=keyboards.tickets_main_kb()
    )


# ОБРАБОТКА ВЫБОРА КОНКРЕТНОГО БИЛЕТА
@router.callback_query(F.data.startswith("ticket_"))
async def ticket_details(callback: types.CallbackQuery):
    index = int(callback.data.split("_")[1]) - 1
    user_id = callback.from_user.id

    tickets = await repo.get_tickets(user_id)

    ticket = tickets[index]

    text = (
        f"✈️ Детали билета:\n\n"
        f"{ticket.from_city} → {ticket.to_city}\n"
        f"{ticket.date}\n\n"
        f"Дополнительная информация будет добавлена позже."
    )

    await callback.message.answer(
        text,
        reply_markup=keyboards.delete_ticket_kb(ticket.id)
    )

    await callback.answer()


# Удаление билета
@router.callback_query(F.data.startswith("delete_"))
async def delete_ticket(callback: types.CallbackQuery):
    ticket_id = int(callback.data.split("_")[1])

    await repo.delete_ticket(ticket_id)

    await callback.message.answer(
        "Билет удалён.",
        reply_markup=keyboards.tickets_main_kb()
    )

    await callback.answer()
