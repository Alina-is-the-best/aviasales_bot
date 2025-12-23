import os
from dotenv import load_dotenv, find_dotenv

# ищем .env и загружаем его
env_path = find_dotenv()
if not env_path:
    raise SystemExit("Переменные окружения не загружены: отсутствует файл .env")
load_dotenv(env_path)

TOKEN = os.getenv("BOT_TOKEN", "8263957137:AAGsOZm7V4N-YLc6tpL71VzHYyLO3TXZRCg")
API_TOKEN = os.getenv("API_TOKEN")