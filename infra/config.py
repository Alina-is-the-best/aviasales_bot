import os
import asyncio

from commands import search
from aiogram import Bot, Dispatcher


# Получаем токены из переменных окружения Docker
TOKEN = os.getenv("BOT_TOKEN")
API_TOKEN = os.getenv("API_TOKEN")

if not TOKEN or not API_TOKEN:
    raise SystemExit(
        "Не заданы обязательные переменные окружения: BOT_TOKEN или API_TOKEN"
    )
