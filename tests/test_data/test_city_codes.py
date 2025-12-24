# tests/test_data/test_city_codes.py

import pytest
from models.data.city_codes import get_city_code


def test_get_city_code_known_city():
    """Тест для известного города"""
    result = get_city_code("Москва")
    assert result == "MOW"  # IATA код Москвы


def test_get_city_code_known_city_lowercase():
    """Тест для известного города в нижнем регистре"""
    result = get_city_code("москва")
    assert result == "MOW"


def test_get_city_code_unknown_city_returns_none():
    """Тест для неизвестного города - должен возвращать None"""
    result = get_city_code("Какой-то город")
    assert result is None  # Ожидаем None, а не строку


def test_get_city_code_partial_match():
    """Тест для частичного совпадения"""
    # Это зависит от реализации - если есть Санкт-Петербург
    result = get_city_code("Санкт-Петербург")
    # Может быть "LED" или None, в зависимости от базы данных
    # Уточните, что должна возвращать функция


def test_get_city_code_empty_string():
    """Тест для пустой строки"""
    result = get_city_code("")
    assert result is None


def test_get_city_code_with_spaces():
    """Тест для города с пробелами"""
    result = get_city_code("  Москва  ")
    assert result == "MOW"  # Должен обрезать пробелы


def test_get_city_code_english_name():
    """Тест для английского названия"""
    result = get_city_code("Moscow")
    assert result == "MOW"  # Если поддерживается английский


def test_get_city_code_case_insensitive():
    """Тест нечувствительности к регистру"""
    result1 = get_city_code("МОСКВА")
    result2 = get_city_code("москва")
    result3 = get_city_code("Москва")
    assert result1 == result2 == result3 == "MOW"


def test_get_city_code_special_characters():
    """Тест для города с дефисом"""
    result = get_city_code("Ростов-на-Дону")
    # Проверьте правильный код для Ростова-на-Дону или None


def test_get_city_code_multiple_words():
    """Тест для многословного названия"""
    result = get_city_code("Новый Уренгой")
    # Проверьте правильный код или None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
