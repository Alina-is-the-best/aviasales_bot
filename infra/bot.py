import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

from infra.keyboards import keyboards
from commands import search
from infra.handlers import tickets, back, help, hot, settings, tracked
from models.data.db import engine, Base
from infra.config import TOKEN


async def main():
    # создает user_filters, которой не хватает
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # регистрация модулей
    search.register(dp)
    hot.register(dp)
    tickets.register(dp)
    settings.register(dp)
    help.register(dp)
    tracked.register(dp)

    dp.include_router(back.back_router)

    @dp.message(Command("start"))
    async def start_cmd(msg: types.Message):
        await msg.answer(
            "Добро пожаловать в Aviasales Bot!\nВыберите действие:",
            reply_markup=keyboards.main_menu()
        )

    print("Bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
