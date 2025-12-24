"""import sys
import pytest

try:
    from adapters.api.aviasales_api import parse_flights
    print("✅ Модуль api успешно импортирован")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print(f"Текущий путь Python: {sys.path}")
    exit(1)

@pytest.mark.asyncio
async def test_parse_flights_returns_dict():
    print("🔍 Тестируем API Aviasales...")
    result = await parse_flights(
        origin="MOW",
        destination="AER",
        depart_date="2025-12-27",
        endpoint="latest"
    )
    assert isinstance(result, dict)
"""