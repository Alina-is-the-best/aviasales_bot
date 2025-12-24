# tests/test_utils_functions.py
import pytest
from unittest.mock import patch
from datetime import datetime
from utils.utils import (
    is_date_in_coming_week,
    format_date_for_api,
    format_date_for_user,
    get_transfers_text,
    format_one_way_ticket,
    format_round_trip_ticket
)


# === Tests for is_date_in_coming_week ===
def test_is_date_in_coming_week_with_mocked_datetime():
    """Тест с моком datetime.now() для фиксированной даты"""
    with patch('utils.utils.datetime') as mock_datetime:
        # Фиксируем текущую дату на 2025-12-15
        fixed_now = datetime(2025, 12, 15, 12, 0, 0)
        fixed_today = fixed_now.date()
        mock_datetime.now.return_value = fixed_now
        mock_datetime.today.return_value = fixed_today
        mock_datetime.fromisoformat.side_effect = datetime.fromisoformat

        # Тесты
        assert is_date_in_coming_week("2025-12-15T10:00:00Z") == True  # Сегодня
        assert is_date_in_coming_week("2025-12-16T10:00:00Z") == True  # Завтра
        assert is_date_in_coming_week("2025-12-20T10:00:00Z") == True  # Через 5 дней
        assert is_date_in_coming_week("2025-12-22T10:00:00Z") == True  # Через 7 дней
        assert is_date_in_coming_week("2025-12-14T10:00:00Z") == False  # Вчера
        assert is_date_in_coming_week("2025-12-23T10:00:00Z") == False  # Через 8 дней
        assert is_date_in_coming_week("2025-12-15") == True  # Дата без времени
        assert is_date_in_coming_week("") == False  # Пустая строка
        assert is_date_in_coming_week(None) == False  # None
        assert is_date_in_coming_week("invalid-date") == False  # Невалидная дата


# === Tests for format_date_for_api ===
@pytest.mark.parametrize("date_str, expected", [
    ("01.01.2025", "2025-01-01"),
    ("15.12.2025", "2025-12-15"),
    ("31.12.2025", "2025-12-31"),
    # Edge cases
    ("", None),
    (None, None),
    ("invalid", None),
    ("1.1.2025", "2025-01-01"),  # Без ведущих нулей
])
def test_format_date_for_api(date_str, expected):
    """Тест преобразования даты из пользовательского формата в API формат."""
    result = format_date_for_api(date_str)
    assert result == expected


# === Tests for format_date_for_user ===
@pytest.mark.parametrize("iso_date, expected", [
    # С временем и часовым поясом
    ("2025-12-15T15:30:00Z", "15.12.2025 15:30"),
    ("2025-12-15T09:15:00", "15.12.2025 09:15"),  # Без 'Z'
    ("2025-12-15T15:30:00.123Z", "15.12.2025 15:30"),  # С миллисекундами
    # Только дата
    ("2025-12-15", "15.12.2025"),
    ("2025-01-01", "01.01.2025"),
    # Edge cases
    ("", "?"),
    (None, "?"),
    ("invalid-date", "invalid-date"),
])
def test_format_date_for_user(iso_date, expected):
    """Тест форматирования ISO даты в читаемый пользовательский формат."""
    result = format_date_for_user(iso_date)
    assert result == expected


# === Tests for get_transfers_text ===
@pytest.mark.parametrize("count, expected", [
    (0, "прямой"),
    (1, "1 пересадка"),
    (2, "2 пересадки"),
    (3, "3 пересадки"),
    (5, "5 пересадки"),  # Проверяем, что для >1 всегда "пересадки"
])
def test_get_transfers_text(count, expected):
    """Тест получения текстового описания количества пересадок."""
    result = get_transfers_text(count)
    assert result == expected


# === Tests for format_one_way_ticket ===
def test_format_one_way_ticket_basic():
    """Тест базового форматирования билета в один конец."""
    flight = {
        'price': 5000,
        'airline': 'SU',
        'departure_at': '2025-12-15T10:00:00Z',
        'number_of_changes': 1
    }
    result = format_one_way_ticket(flight, "Москва", "Сочи")

    assert "SU" in result
    assert "Москва → Сочи" in result
    assert "15.12.2025 10:00" in result
    assert "1 пересадка" in result
    assert "5000₽" in result


def test_format_one_way_ticket_with_index():
    """Тест форматирования с нумерацией."""
    flight = {
        'price': 7000,
        'airline_iata': 'S7',  # Альтернативное поле
        'departure_at': '2025-12-16T12:00:00Z',
        'transfers': 0  # Альтернативное поле для пересадок
    }
    result = format_one_way_ticket(flight, "Москва", "Казань", index=1)

    assert "1. " in result  # Проверка префикса
    assert "S7" in result
    assert "прямой" in result
    assert "7000₽" in result


def test_format_one_way_ticket_fallback_fields():
    """Тест с запасными полями (value вместо price)."""
    flight = {
        'value': 3000,  # Запасное поле
        'airline': 'U6',
        'departure_at': '2025-12-17T08:00:00Z'
    }
    result = format_one_way_ticket(flight, "Москва", "Екатеринбург")

    assert "U6" in result
    assert "3000₽" in result
    assert "прямой" in result  # Значение по умолчанию для отсутствующего поля - 0, должно быть "прямой"


def test_format_one_way_ticket_missing_all_fields():
    """Тест с минимальными данными."""
    flight = {
        'airline': 'TEST'
    }
    result = format_one_way_ticket(flight, "Город1", "Город2")

    # Проверяем, что функция не падает и формирует что-то разумное
    assert "TEST" in result
    assert "Город1 → Город2" in result
    assert "? (" in result  # Дата должна быть "?" при отсутствии departure_at
    assert "0₽" in result  # Цена по умолчанию 0


# === Tests for format_round_trip_ticket ===
def test_format_round_trip_ticket_basic():
    """Тест форматирования билета туда-обратно."""
    flight_there = {
        'price': 5000,
        'departure_at': '2025-12-15T10:00:00Z',
        'transfers': 1
    }
    flight_back = {
        'price': 4500,
        'departure_at': '2025-12-20T18:00:00Z',
        'transfers': 0
    }

    result = format_round_trip_ticket(flight_there, flight_back, "Москва", "Сочи")

    assert "Туда-обратно" in result
    assert "Москва ↔ Сочи" in result
    assert "Всего: 9500₽" in result
    assert "Туда: 15.12.2025 10:00 (1 пересадка)" in result
    assert "Обратно: 20.12.2025 18:00 (прямой)" in result


def test_format_round_trip_ticket_with_index():
    """Тест форматирования туда-обратно с нумерацией."""
    flight_there = {'price': 4000, 'departure_at': '2025-12-15T10:00:00Z', 'transfers': 0}
    flight_back = {'price': 3500, 'departure_at': '2025-12-18T20:00:00Z', 'transfers': 1}

    result = format_round_trip_ticket(flight_there, flight_back, "Москва", "Казань", index=2)

    assert "2. " in result
    assert "Всего: 7500₽" in result


def test_format_round_trip_ticket_missing_data():
    """Тест с отсутствующими данными (проверка устойчивости)."""
    flight_there = {'price': 5000, 'departure_at': '2025-12-15T10:00:00Z'}  # Нет transfers
    flight_back = {'departure_at': '2025-12-20T18:00:00Z'}  # Нет price

    result = format_round_trip_ticket(flight_there, flight_back, "Москва", "Сочи")

    # Проверяем, что функция не падает и формирует что-то разумное
    assert "Москва ↔ Сочи" in result
    # Цена туда должна быть 5000, обратно - 0 (по умолчанию), итого 5000
    assert "Всего: 5000₽" in result


# Дополнительные тесты для edge cases
def test_format_date_for_user_handles_different_formats():
    """Тест обработки различных форматов дат."""
    with patch('utils.utils.datetime') as mock_datetime:
        # Мокаем только fromisoformat для теста
        def mock_fromisoformat(date_str):
            if date_str == "2025-12-15T10:00:00":
                return datetime(2025, 12, 15, 10, 0, 0)
            raise ValueError

        mock_datetime.fromisoformat.side_effect = mock_fromisoformat
        mock_datetime.strptime = datetime.strptime

        result = format_date_for_user("2025-12-15T10:00:00")
        assert result == "15.12.2025 10:00"


def test_is_date_in_coming_week_handles_timezone():
    """Тест обработки дат с часовыми поясами."""
    with patch('utils.utils.datetime') as mock_datetime:
        # Фиксируем текущую дату
        fixed_now = datetime(2025, 12, 15, 12, 0, 0)
        fixed_today = fixed_now.date()
        mock_datetime.now.return_value = fixed_now
        mock_datetime.today.return_value = fixed_today

        # Мокаем fromisoformat для обработки Z
        def mock_fromisoformat(date_str):
            clean_str = date_str.replace('Z', '')
            return datetime.fromisoformat(clean_str)

        mock_datetime.fromisoformat.side_effect = mock_fromisoformat

        assert is_date_in_coming_week("2025-12-15T14:00:00Z") == True
        assert is_date_in_coming_week("2025-12-22T23:59:59Z") == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])