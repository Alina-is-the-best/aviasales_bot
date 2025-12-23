from api.functions import (
    filter_by_price,
    filter_by_baggage,
    filter_by_stops,
    filter_by_airline
)

def test_filter_by_price():
    """
    Проверяем:
    - что остаются только рейсы с ценой <= max_price
    """
    flights = [
        {"price": 5000},
        {"price": 12000},
        {"price": 8000},
    ]

    result = filter_by_price(flights, max_price=9000)

    assert len(result) == 2
    assert all(f["price"] <= 9000 for f in result)

def test_filter_by_baggage():
    """
    Проверяем:
    - отбор рейсов по наличию багажа
    """
    flights = [
        {"bags_included": True},
        {"bags_included": False},
        {"bags_included": True},
    ]

    result = filter_by_baggage(flights, baggage_included=True)

    assert len(result) == 2
    assert all(f["bags_included"] is True for f in result)


def test_filter_by_stops():
    """
    Проверяем:
    - что количество пересадок не превышает max_stops
    """
    flights = [
        {"number_of_changes": 0},
        {"number_of_changes": 1},
        {"number_of_changes": 2},
    ]

    result = filter_by_stops(flights, max_stops=1)

    assert len(result) == 2
    assert all(f["number_of_changes"] <= 1 for f in result)


def test_filter_by_airline():
    """
    Проверяем:
    - что остаются рейсы только разрешённых авиакомпаний
    """
    flights = [
        {"airline": "SU"},
        {"airline": "S7"},
        {"airline": "U6"},
    ]

    result = filter_by_airline(flights, allowed_airlines=["SU", "S7"])

    assert len(result) == 2
    assert all(f["airline"] in ["SU", "S7"] for f in result)
