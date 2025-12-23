from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from keyboards import keyboards

back_router = Router()

@back_router.message(F.text == "⬅️ Назад в меню")
async def back_to_main(msg: types.Message, state: FSMContext):
    if await state.get_state() is not None:
        return

    await msg.answer(
        "Главное меню:",
        reply_markup=keyboards.main_menu()
    )
