from models.data.city_codes import get_city_code


def test_get_city_code_known_city():
    assert get_city_code("Москва") == "MOW"


def test_get_city_code_lowercase():
    assert get_city_code("москва") == "MOW"


def test_get_city_code_unknown_city_returns_uppercase():
    result = get_city_code("Какой-то город")
    assert result == "КАКОЙ-ТО ГОРОД"

