from aiogram import Router, types, F
from infra.keyboards import keyboards

router = Router()

def register(dp):
    dp.include_router(router)


@router.message(F.text == "Что я умею")
async def help_menu(msg: types.Message):
    text = (
        "💡 Я умею:\n\n"
        "• Показывать горячие билеты 🔥\n"
        "• Искать билеты по простому маршруту ✈️\n"
        "• Искать билеты по сложному маршруту 🧩\n"
        "• Помогать выбрать даты через календарь 📅\n"
        "• Собирать запрос поиска и готовить его для API\n"
        "Выберите действие из меню 👇"
    )

    await msg.answer(text, reply_markup=keyboards.main_menu())
