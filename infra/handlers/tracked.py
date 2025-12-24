from aiogram import Router, types, F
from infra.keyboards import keyboards
from models.repo import tracked_repository as repo
from models.data.city_codes import get_city_code
from adapters.api.aviasales_api import parse_flights
from utils.utils import format_one_way_ticket, format_date_for_api

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

@router.callback_query(F.data.startswith("track_delete_"))
async def tracked_delete(callback: types.CallbackQuery):
    try:
        # Извлекаем ID, забирая последнюю часть строки
        ticket_id = int(callback.data.split("_")[-1])
        await repo.delete_tracked(ticket_id)
        await callback.message.answer("Билет удалён из отслеживаемых.", reply_markup=keyboards.main_menu())
    except Exception as e:
        await callback.answer("Ошибка при удалении", show_alert=True)
    await callback.answer()

# Просмотр билета
@router.callback_query(F.data.startswith("track_"))
async def tracked_ticket_details(callback: types.CallbackQuery):
    index = int(callback.data.split("_")[1]) - 1
    tickets = await repo.get_tracked(callback.from_user.id)
    ticket = tickets[index]

    text = f"📍 **Данные билета:**\n{ticket.from_city} → {ticket.to_city}\n"
    text += f"📅 Дата: {ticket.date_from}\n"
    text += f"💰 Ваш лимит: {ticket.price_limit}₽\n\n"

    # поиск самого дешевого билета
    await callback.answer("Обновляю цену... 🔎")
    origin_code = get_city_code(ticket.from_city)
    dest_code = get_city_code(ticket.to_city)
    api_date = format_date_for_api(ticket.date_from)

    if origin_code and dest_code:
        result = await parse_flights(origin=origin_code, destination=dest_code, depart_date=api_date)
        flights = result.get('data', [])
        if flights:
            cheapest = min(flights, key=lambda x: x.get('price', float('inf')))
            text += "✅ **Самый дешевый сейчас:**\n"
            text += format_one_way_ticket(cheapest, ticket.from_city, ticket.to_city)
        else:
            text += "😔 Билетов на эту дату не найдено."

    await callback.message.answer(
        text, 
        reply_markup=keyboards.tracked_delete_kb(ticket.id),
        parse_mode="Markdown"
    )
    await callback.answer()