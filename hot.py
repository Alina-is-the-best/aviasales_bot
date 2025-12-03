from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

import keyboards
from states import HotTickets

router = Router()

def register(dp):
    dp.include_router(router)


# Первый шаг — выбираем город
@router.message(F.text == "Горячие билеты")
async def hot_start(msg: types.Message, state: FSMContext):
    await state.set_state(HotTickets.from_city)
    await msg.answer(
        "Откуда летим?",
        reply_markup=keyboards.back_to_main()
    )


# Второй шаг — ловим введённый город
@router.message(HotTickets.from_city)
async def hot_city_received(msg: types.Message, state: FSMContext):
    if msg.text == "⬅️ Назад в меню":
        await state.clear()
        return await msg.answer("Главное меню:", reply_markup=keyboards.main_menu())

    user_city = msg.text.strip()

    await state.update_data(from_city=user_city)

    # Здесь позже подключим Aviasales API 🔥
    await msg.answer(
        f"Ищу горячие билеты из: {user_city} 🔥\n\n"
        f"(Позже подключу Aviasales API)",
        reply_markup=keyboards.main_menu()
    )

    await state.clear()
