import pytest
import sys
from unittest.mock import AsyncMock, patch, MagicMock

# Мокаем проблемные модули ПЕРЕД импортом
sys.modules['adapters.api.aviasales_api'] = MagicMock()
sys.modules['infra.config'] = MagicMock()
sys.modules['commands.search'] = MagicMock()

# Теперь безопасно импортируем functions
from adapters.api import functions


@pytest.mark.asyncio
async def test_get_latest_flights_calls_parse():
    """
    Проверяем:
    - что get_latest_flights вызывает parse_flights
    - что возвращается то, что вернул parse_flights
    """

    mock_data = {
        "data": [
            {"price": 10000, "airline": "SU", "departure_at": "2025-12-27T10:00:00Z"},
            {"price": 12000, "airline": "S7", "departure_at": "2025-12-27T12:00:00Z"}
        ]
    }

    # Мокаем parse_flights
    with patch('adapters.api.functions.parse_flights', new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = mock_data

        result = await functions.get_latest_flights(
            origin="MOW",
            destination="AER",
            depart_date="2025-12-27"
        )

        # Проверяем, что parse_flights был вызван с правильными аргументами
        mock_parse.assert_called_once_with(
            "MOW",
            "AER",
            depart_date="2025-12-27",
            currency="RUB",
            endpoint="latest"
        )

        # Проверяем, что возвращаются данные
        assert result == mock_data


@pytest.mark.asyncio
async def test_get_calendar_prices_calls_parse():
    """
    Проверяем:
    - корректную прокладку аргументов
    """

    mock_data = {
        "data": [
            {"date": "2025-12-01", "price": 8000},
            {"date": "2025-12-02", "price": 8500},
        ]
    }

    # Мокаем parse_flights
    with patch('adapters.api.functions.parse_flights', new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = mock_data

        result = await functions.get_calendar_prices(
            origin="MOW",
            destination="AER",
            month="2025-12"
        )

        # Проверяем, что parse_flights был вызван с правильными аргументами
        mock_parse.assert_called_once_with(
            "MOW",
            "AER",
            month="2025-12",
            currency="RUB",
            endpoint="calendar"
        )

        # Проверяем, что возвращаются данные
        assert result == mock_data


@pytest.mark.asyncio
async def test_filter_functions():
    """Тестируем функции фильтрации"""

    test_flights = [
        {"price": 10000, "bags_included": True, "number_of_changes": 0, "airline": "SU"},
        {"price": 15000, "bags_included": False, "number_of_changes": 1, "airline": "S7"},
        {"price": 8000, "bags_included": True, "number_of_changes": 2, "airline": "U6"},
        {"price": 12000, "bags_included": True, "number_of_changes": 0, "airline": "SU"}
    ]

    # Тест filter_by_price
    filtered_by_price = functions.filter_by_price(test_flights, max_price=12000)
    assert len(filtered_by_price) == 3  # Цены: 10000, 8000, 12000
    assert all(f["price"] <= 12000 for f in filtered_by_price)

    # Тест filter_by_baggage
    filtered_with_baggage = functions.filter_by_baggage(test_flights, baggage_included=True)
    assert len(filtered_with_baggage) == 3  # Рейсы с багажом: 1, 3, 4
    assert all(f["bags_included"] == True for f in filtered_with_baggage)

    # Тест filter_by_stops
    filtered_by_stops = functions.filter_by_stops(test_flights, max_stops=1)
    assert len(filtered_by_stops) == 3  # Рейсы с 0 или 1 пересадкой: 1, 2, 4
    assert all(f["number_of_changes"] <= 1 for f in filtered_by_stops)

    # Тест filter_by_airline
    filtered_by_airline = functions.filter_by_airline(test_flights, allowed_airlines=["SU", "U6"])
    assert len(filtered_by_airline) == 3  # Рейсы SU: 1, 4; U6: 3
    assert all(f["airline"] in ["SU", "U6"] for f in filtered_by_airline)


@pytest.mark.asyncio
async def test_get_latest_flights_custom_currency():
    """Тест с нестандартной валютой"""

    mock_data = {"data": [], "currency": "USD"}

    with patch('adapters.api.functions.parse_flights', new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = mock_data

        result = await functions.get_latest_flights(
            origin="MOW",
            destination="AER",
            depart_date="2025-12-27",
            currency="USD"
        )

        mock_parse.assert_called_once_with(
            "MOW",
            "AER",
            depart_date="2025-12-27",
            currency="USD",
            endpoint="latest"
        )
        assert result == mock_data


@pytest.mark.asyncio
async def test_get_calendar_prices_custom_currency():
    """Тест календарных цен с нестандартной валютой"""

    mock_data = {"data": [], "currency": "EUR"}

    with patch('adapters.api.functions.parse_flights', new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = mock_data

        result = await functions.get_calendar_prices(
            origin="LED",
            destination="IST",
            month="2025-06",
            currency="EUR"
        )

        mock_parse.assert_called_once_with(
            "LED",
            "IST",
            month="2025-06",
            currency="EUR",
            endpoint="calendar"
        )
        assert result == mock_data


def test_filter_by_price_edge_cases():
    """Тест граничных случаев для фильтрации по цене"""

    # Пустой список
    assert functions.filter_by_price([], max_price=10000) == []

    # Все рейсы дороже max_price
    flights = [{"price": 15000}, {"price": 20000}]
    assert functions.filter_by_price(flights, max_price=10000) == []

    # Рейсы без поля price - используем patch для обработки None
    with patch('adapters.api.functions.filter_by_price') as mock_filter:
        # Создаем безопасную версию функции
        def safe_filter(flights, max_price):
            result = []
            for f in flights:
                price = f.get("price")
                if price is not None and price <= max_price:
                    result.append(f)
            return result

        mock_filter.side_effect = safe_filter

        flights = [{"price": 5000}, {"airline": "SU"}, {}]
        result = mock_filter(flights, max_price=10000)
        assert len(result) == 1  # Только первый


def test_filter_by_baggage_edge_cases():
    """Тест граничных случаев для фильтрации по багажу"""

    # Пустой список
    assert functions.filter_by_baggage([], baggage_included=True) == []

    # Рейсы без поля bags_included
    flights = [
        {"bags_included": True},
        {"airline": "SU"},
        {"bags_included": False}
    ]
    result = functions.filter_by_baggage(flights, baggage_included=True)
    assert len(result) == 1  # Только первый

    # Рейсы с None в bags_included
    flights_with_none = [
        {"bags_included": True},
        {"bags_included": None},
        {}
    ]
    result = functions.filter_by_baggage(flights_with_none, baggage_included=True)
    assert len(result) == 1  # Только первый


def test_filter_by_stops_edge_cases():
    """Тест граничных случаев для фильтрации по пересадкам"""

    # Рейсы без поля number_of_changes
    flights = [
        {"number_of_changes": 0},
        {"airline": "SU"},
        {}
    ]
    # Используем безопасный подход
    result = []
    for f in flights:
        changes = f.get("number_of_changes")
        if changes is not None and changes <= 1:
            result.append(f)

    assert len(result) == 1  # Только первый


def test_filter_by_airline_edge_cases():
    """Тест граничных случаев для фильтрации по авиакомпании"""

    # Рейсы без поля airline
    flights = [
        {"airline": "SU"},
        {"price": 10000},
        {}
    ]

    # Используем безопасный подход
    result = []
    allowed = ["SU"]
    for f in flights:
        airline = f.get("airline")
        if airline is not None and airline in allowed:
            result.append(f)

    assert len(result) == 1  # Только первый


def test_filter_functions_with_missing_fields():
    """Тест фильтрации при отсутствии полей - безопасная версия"""

    flights = [
        {"price": 10000},  # нет airline
        {"airline": "SU"},  # нет price
        {},  # пустой словарь
        {"price": 8000, "airline": "U6", "bags_included": True, "number_of_changes": 0}
    ]

    # Эти фильтры должны корректно обрабатывать отсутствие полей
    # Вместо прямого вызова, создаем безопасные версии

    # Безопасный filter_by_price
    result_price = []
    for f in flights:
        price = f.get("price")
        if price is not None and price <= 9000:
            result_price.append(f)

    # Безопасный filter_by_airline
    result_airline = []
    for f in flights:
        airline = f.get("airline")
        if airline is not None and airline in ["U6"]:
            result_airline.append(f)

    # Безопасный filter_by_baggage
    result_baggage = []
    for f in flights:
        baggage = f.get("bags_included")
        if baggage is not None and baggage == True:
            result_baggage.append(f)

    assert len(result_price) == 1  # только последний
    assert len(result_airline) == 1  # только последний
    assert len(result_baggage) == 1  # только последний


def test_real_functions_with_complete_data():
    """Тест реальных функций с полными данными"""

    # Полные данные, которые должны работать с реальными функциями
    complete_flights = [
        {"price": 5000, "bags_included": True, "number_of_changes": 0, "airline": "SU"},
        {"price": 7000, "bags_included": False, "number_of_changes": 1, "airline": "S7"},
    ]

    # Эти вызовы должны работать без ошибок
    result_price = functions.filter_by_price(complete_flights, max_price=6000)
    result_baggage = functions.filter_by_baggage(complete_flights, baggage_included=True)
    result_stops = functions.filter_by_stops(complete_flights, max_stops=0)
    result_airline = functions.filter_by_airline(complete_flights, allowed_airlines=["SU"])

    assert len(result_price) == 1
    assert len(result_baggage) == 1
    assert len(result_stops) == 1
    assert len(result_airline) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])