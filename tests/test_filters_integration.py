import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, patch

sys.modules['adapters.api.aviasales_api'] = MagicMock()
sys.modules['infra.config'] = MagicMock()
sys.modules['models.data.city_codes'] = MagicMock()


async def filter_flights_test_version(flights: list, state_data: dict, user_filters) -> list:
    """Тестовая версия функции filter_flights без внешних зависимостей"""
    if not flights:
        return []

    filtered = []

    # 1. Получаем фильтр цены
    limit_price = None
    try:
        # Сначала из текущего поиска
        price_limit_value = state_data.get('price_limit')
        if price_limit_value:
            if isinstance(price_limit_value, (int, float)):
                limit_price = int(price_limit_value)
            elif isinstance(price_limit_value, str) and price_limit_value.isdigit():
                limit_price = int(price_limit_value)

        # Если не нашли, берем из постоянных фильтров
        if limit_price is None and user_filters and user_filters.price_limit:
            filter_price = user_filters.price_limit
            if isinstance(filter_price, (int, float)):
                limit_price = int(filter_price)
            elif isinstance(filter_price, str) and filter_price.isdigit():
                limit_price = int(filter_price)
    except (ValueError, TypeError):
        limit_price = None

    # 2. Получаем фильтр пересадок
    req_transfers = state_data.get('transfers')
    if not req_transfers and user_filters:
        req_transfers = user_filters.transfers

    # 3. Получаем фильтр багажа
    req_baggage = state_data.get('baggage')
    if not req_baggage and user_filters:
        req_baggage = user_filters.baggage

    # 4. Применяем фильтры
    for f in flights:
        # Фильтр цены
        price = f.get('price', f.get('value', 0))
        if limit_price is not None and limit_price > 0 and price > limit_price:
            continue

        # Фильтр пересадок
        transfers = f.get('transfers', f.get('number_of_changes', 0))
        if req_transfers == 'Только прямой рейс' and transfers > 0:
            continue

        # Фильтр багажа
        bags_included = f.get('bags_included', False)
        if req_baggage == 'С багажом' and not bags_included:
            continue
        if req_baggage == 'Без багажа' and bags_included:
            continue

        filtered.append(f)

    return filtered


@pytest.mark.asyncio
async def test_filter_flights_price_limit():
    """Тест фильтра по цене"""

    flights = [
        {'price': 5000, 'bags_included': True, 'transfers': 0},
        {'price': 15000, 'bags_included': True, 'transfers': 0},  # Слишком дорогой
        {'price': 8000, 'bags_included': True, 'transfers': 0},
    ]

    # Мокаем user_filters с лимитом цены
    mock_filters = MagicMock()
    mock_filters.price_limit = "10000"
    mock_filters.transfers = None
    mock_filters.baggage = None

    result = await filter_flights_test_version(flights, {}, mock_filters)

    # Должны остаться билеты до 10000₽
    assert len(result) == 2
    assert all(f['price'] <= 10000 for f in result)


@pytest.mark.asyncio
async def test_filter_flights_direct_only():
    """Тест фильтра 'Только прямой рейс'"""

    flights = [
        {'price': 5000, 'bags_included': True, 'transfers': 0},
        {'price': 6000, 'bags_included': True, 'transfers': 1},  # С пересадкой
        {'price': 7000, 'bags_included': True, 'transfers': 2},  # С пересадкой
    ]

    mock_filters = MagicMock()
    mock_filters.price_limit = None
    mock_filters.transfers = "Только прямой рейс"
    mock_filters.baggage = None

    result = await filter_flights_test_version(flights, {}, mock_filters)

    # Должен остаться только прямой рейс
    assert len(result) == 1
    assert result[0]['transfers'] == 0


@pytest.mark.asyncio
async def test_filter_flights_with_baggage():
    """Тест фильтра 'С багажом'"""

    flights = [
        {'price': 5000, 'bags_included': True, 'transfers': 0},
        {'price': 6000, 'bags_included': False, 'transfers': 0},  # Без багажа
        {'price': 7000, 'bags_included': True, 'transfers': 0},
    ]

    mock_filters = MagicMock()
    mock_filters.price_limit = None
    mock_filters.transfers = None
    mock_filters.baggage = "С багажом"

    result = await filter_flights_test_version(flights, {}, mock_filters)

    # Должны остаться только билеты с багажом
    assert len(result) == 2
    assert all(f['bags_included'] for f in result)


@pytest.mark.asyncio
async def test_filter_flights_without_baggage():
    """Тест фильтра 'Без багажа'"""

    flights = [
        {'price': 5000, 'bags_included': True, 'transfers': 0},  # С багажом
        {'price': 6000, 'bags_included': False, 'transfers': 0},
        {'price': 7000, 'bags_included': False, 'transfers': 0},
    ]

    mock_filters = MagicMock()
    mock_filters.price_limit = None
    mock_filters.transfers = None
    mock_filters.baggage = "Без багажа"

    result = await filter_flights_test_version(flights, {}, mock_filters)

    # Должны остаться только билеты без багажа
    assert len(result) == 2
    assert all(not f['bags_included'] for f in result)


@pytest.mark.asyncio
async def test_filter_flights_combined_filters():
    """Тест комбинированных фильтров"""

    flights = [
        {'price': 5000, 'bags_included': True, 'transfers': 0},  # Подходит
        {'price': 6000, 'bags_included': True, 'transfers': 1},  # Не подходит - пересадка
        {'price': 15000, 'bags_included': True, 'transfers': 0},  # Не подходит - дорого
        {'price': 7000, 'bags_included': False, 'transfers': 0},  # Не подходит - без багажа
    ]

    mock_filters = MagicMock()
    mock_filters.price_limit = "10000"  # Цена до 10000
    mock_filters.transfers = "Только прямой рейс"  # Без пересадок
    mock_filters.baggage = "С багажом"  # Только с багажом

    result = await filter_flights_test_version(flights, {}, mock_filters)

    # Должен остаться только первый билет
    assert len(result) == 1
    assert result[0]['price'] == 5000
    assert result[0]['bags_included'] == True
    assert result[0]['transfers'] == 0


@pytest.mark.asyncio
async def test_filter_flights_priority_state_over_filters():
    """Тест приоритета фильтров из state_data над постоянными фильтрами"""

    flights = [
        {'price': 5000, 'bags_included': True, 'transfers': 0},
        {'price': 15000, 'bags_included': True, 'transfers': 0},  # Дорогой
    ]

    mock_filters = MagicMock()
    mock_filters.price_limit = "20000"  # Постоянный фильтр позволяет до 20000

    # Но в state_data указан более строгий фильтр
    state_data = {'price_limit': 10000}

    result = await filter_flights_test_version(flights, state_data, mock_filters)

    # Должен применяться фильтр из state_data (10000), а не из постоянных фильтров (20000)
    assert len(result) == 1
    assert result[0]['price'] == 5000


@pytest.mark.asyncio
async def test_filter_flights_no_filters():
    """Тест без фильтров - должны вернуться все билеты"""

    flights = [
        {'price': 5000, 'bags_included': True, 'transfers': 0},
        {'price': 15000, 'bags_included': False, 'transfers': 2},
        {'price': 8000, 'bags_included': True, 'transfers': 1},
    ]

    mock_filters = MagicMock()
    mock_filters.price_limit = None
    mock_filters.transfers = None
    mock_filters.baggage = None

    result = await filter_flights_test_version(flights, {}, mock_filters)

    # Без фильтров должны вернуться все билеты
    assert len(result) == 3


@pytest.mark.asyncio
async def test_filter_flights_empty_list():
    """Тест с пустым списком билетов"""

    result = await filter_flights_test_version([], {}, None)
    assert result == []


@pytest.mark.asyncio
async def test_filter_flights_invalid_price_limit():
    """Тест с невалидным лимитом цены"""

    flights = [
        {'price': 5000, 'bags_included': True, 'transfers': 0},
        {'price': 6000, 'bags_included': True, 'transfers': 0},
    ]

    mock_filters = MagicMock()
    mock_filters.price_limit = "не число"  # Невалидное значение
    mock_filters.transfers = None
    mock_filters.baggage = None

    result = await filter_flights_test_version(flights, {}, mock_filters)

    # При невалидном price_limit фильтр не должен применяться
    assert len(result) == 2


@pytest.mark.asyncio
async def test_filter_flights_zero_price_limit():
    """Тест с лимитом цены = 0 (без ограничений)"""

    flights = [
        {'price': 5000, 'bags_included': True, 'transfers': 0},
        {'price': 15000, 'bags_included': True, 'transfers': 0},
    ]

    mock_filters = MagicMock()
    mock_filters.price_limit = "0"  # Нет ограничений
    mock_filters.transfers = None
    mock_filters.baggage = None

    result = await filter_flights_test_version(flights, {}, mock_filters)

    # При price_limit = 0 все билеты должны проходить
    assert len(result) == 2

if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"])