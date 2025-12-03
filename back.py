from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
import keyboards

back_router = Router()

@back_router.message(F.text == "⬅️ Назад в меню")
async def back_to_main(msg: types.Message, state: FSMContext):
    # если FSM активно — его очистят обработчики в других файлах
    if await state.get_state() is not None:
        return

    # если FSM не активно — просто вернём главное меню
    await msg.answer(
        "Главное меню:",
        reply_markup=keyboards.main_menu()
    )
