from aiogram import Router, types, F
from infra.keyboards import keyboards
from models.repo import tracked_repository as repo

router = Router()

def register(dp):
    dp.include_router(router)


# Открытие раздела
@router.message(F.text == "Отслеживаемые билеты")
async def tracked_main(msg: types.Message):
    tickets = await repo.get_tracked(msg.from_user.id)

    # если пусто отправляем одно сообщение
    if not tickets:
        await msg.answer("У вас пока нет отслеживаемых билетов.")
        return

    # если есть билеты
    text = "Ваши отслеживаемые билеты:\n\n"
    for i, t in enumerate(tickets, 1):
        if t.date_to:
            text += f"{i}. {t.from_city} – {t.to_city}\n{t.date_from} → {t.date_to}\n\n"
        else:
            text += f"{i}. {t.from_city} – {t.to_city}\n{t.date_from}\n\n"

    await msg.answer(text)

    await msg.answer(
        "Выберите билет:",
        reply_markup=keyboards.tracked_ticket_numbers(len(tickets))
    )

    await msg.answer(
        "Добавьте новый билет для отслеживания:",
        reply_markup=keyboards.tracked_add_button()
    )

# Добавление билета
async def add_tracked_ticket(msg: types.Message, user_id: int, data: dict):

    if data.get("dates"):
        # one-way
        date_from = data["dates"]
        date_to = ""
    else:
        # round-trip
        date_from = data["depart_date"]
        date_to = data["return_date"]

    await repo.add_tracked(
        user_id=user_id,
        from_city=data["from_city"],
        to_city=data["to_city"],
        date_from=date_from,
        date_to=date_to,
        baggage=data["baggage"],
        transfers=data["transfers"],
        price_limit=data["price_limit"]
    )

    await msg.answer("Билет добавлен в отслеживаемые 👀", reply_markup=keyboards.main_menu())


# Просмотр билета
@router.callback_query(F.data.startswith("track_"))
async def tracked_ticket_details(callback: types.CallbackQuery):
    index = int(callback.data.split("_")[1]) - 1
    tickets = await repo.get_tracked(callback.from_user.id)
    ticket = tickets[index]

    text = f"Данные билета:\n\n{ticket.from_city} → {ticket.to_city}\n"

    if ticket.date_to:
        text += f"{ticket.date_from} → {ticket.date_to}\n"
    else:
        text += f"{ticket.date_from}\n"

    text += (
        f"\nБагаж: {ticket.baggage}"
        f"\nПересадки: {ticket.transfers}"
        f"\nЦена: до {ticket.price_limit}₽"
    )

    await callback.message.answer(text, reply_markup=keyboards.tracked_delete_kb(ticket.id))
    await callback.answer()


# Удаление
@router.callback_query(F.data.startswith("track_delete_"))
async def tracked_delete(callback: types.CallbackQuery):
    ticket_id = int(callback.data.split("_")[3])
    await repo.delete_tracked(ticket_id)

    await callback.message.answer("Билет удалён из отслеживаемых.", reply_markup=keyboards.main_menu())
    await callback.answer()

