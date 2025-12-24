import pytest
from aiogram.types import ReplyKeyboardMarkup

from infra.keyboards.keyboards import (
    main_menu,
    route_type_menu,
    back_to_main,
    trip_type_kb,
    calendar_kb,
    baggage_kb,
    transfers_kb,
    complex_add_more_kb,
    tickets_main_kb,
    add_ticket_button,
    tickets_numbers_kb,
    delete_ticket_kb,
    tracked_main_kb,
    tracked_add_button,
    tracked_ticket_numbers,
    tracked_delete_kb,
    settings_menu,
    filters_menu,
    filters_delete_kb,
    filter_baggage_kb,
    filter_transfers_kb,
    hot_dest_kb
)

def test_route_type_menu():
    """Тест меню выбора типа маршрута"""
    kb = route_type_menu()
    assert kb.resize_keyboard == True
    assert len(kb.keyboard) == 3

    texts = [row[0].text for row in kb.keyboard]
    assert texts == ["Простой маршрут", "Сложный маршрут", "⬅️ Назад в меню"]


def test_back_to_main():
    """Тест кнопки 'Назад в меню'"""
    kb = back_to_main()
    assert kb.resize_keyboard == True
    assert len(kb.keyboard) == 1
    assert len(kb.keyboard[0]) == 1
    assert kb.keyboard[0][0].text == "⬅️ Назад в меню"


def test_trip_type_kb():
    """Тест клавиатуры типа поездки"""
    kb = trip_type_kb()
    assert kb.resize_keyboard == True
    assert len(kb.keyboard) == 3

    texts = [row[0].text for row in kb.keyboard]
    assert texts == ["В одну сторону", "Туда-обратно", "⬅️ Назад в меню"]


def test_calendar_kb():
    """Тест клавиатуры календаря"""
    kb = calendar_kb()
    assert kb.resize_keyboard == True
    assert len(kb.keyboard) == 2

    texts = [row[0].text for row in kb.keyboard]
    assert texts == ["📅 Календарь", "⬅️ Назад в меню"]


def test_baggage_kb():
    """Тест клавиатуры выбора багажа"""
    kb = baggage_kb()
    assert kb.resize_keyboard == True
    assert len(kb.keyboard) == 3

    texts = [row[0].text for row in kb.keyboard]
    assert texts == ["С багажом", "Без багажа", "⬅️ Назад в меню"]


def test_transfers_kb():
    """Тест клавиатуры выбора пересадок"""
    kb = transfers_kb()
    assert kb.resize_keyboard == True
    assert len(kb.keyboard) == 3

    texts = [row[0].text for row in kb.keyboard]
    assert texts == ["Только прямой", "Любой подойдет", "⬅️ Назад в меню"]


def test_complex_add_more_kb():
    """Тест клавиатуры добавления сегментов"""
    kb = complex_add_more_kb()
    assert kb.resize_keyboard == True
    assert len(kb.keyboard) == 3

    texts = [row[0].text for row in kb.keyboard]
    assert texts == ["➕ Добавить сегмент", "✔ Завершить маршрут", "⬅️ Назад в меню"]


def test_settings_menu():
    """Тест меню настроек"""
    kb = settings_menu()
    assert kb.resize_keyboard == True
    assert len(kb.keyboard) == 3

    texts = [row[0].text for row in kb.keyboard]
    assert texts == ["Валюта", "Постоянные фильтры", "⬅️ Назад в меню"]


def test_filters_menu():
    """Тест меню фильтров"""
    kb = filters_menu()
    assert kb.resize_keyboard == True
    assert len(kb.keyboard) == 5

    texts = [row[0].text for row in kb.keyboard]
    assert texts == ["Место вылета ✈️", "Багаж 🎒", "Пересадки ↩️",
                     "Ценовые ограничения 💴", "⬅️ Назад в меню"]


def test_filters_delete_kb():
    """Тест клавиатуры удаления фильтра"""
    kb = filters_delete_kb("багаж")
    assert kb.resize_keyboard == True
    assert len(kb.keyboard) == 2

    assert kb.keyboard[0][0].text == "Удалить фильтр (багаж)"
    assert kb.keyboard[1][0].text == "⬅️ Назад в меню"


def test_filter_baggage_kb():
    """Тест клавиатуры фильтра багажа"""
    kb = filter_baggage_kb()
    assert kb.resize_keyboard == True
    assert len(kb.keyboard) == 3

    # Первая строка: две кнопки в ряд
    assert len(kb.keyboard[0]) == 2
    assert kb.keyboard[0][0].text == "С багажом"
    assert kb.keyboard[0][1].text == "Без багажа"

    # Вторая и третья строки: по одной кнопке
    assert kb.keyboard[1][0].text == "Удалить фильтр (багаж)"
    assert kb.keyboard[2][0].text == "⬅️ Назад в меню"


def test_filter_transfers_kb():
    """Тест клавиатуры фильтра пересадок"""
    kb = filter_transfers_kb()
    assert kb.resize_keyboard == True
    assert len(kb.keyboard) == 4

    texts = [row[0].text for row in kb.keyboard]
    assert texts == ["Только прямой рейс", "Любые пересадки",
                     "Удалить фильтр (пересадки)", "⬅️ Назад в меню"]


def test_hot_dest_kb():
    """Тест клавиатуры горячих билетов"""
    kb = hot_dest_kb()
    assert kb.resize_keyboard == True
    assert len(kb.keyboard) == 2

    texts = [row[0].text for row in kb.keyboard]
    assert texts == ["🌍 Куда угодно", "⬅️ Назад в меню"]


def test_add_ticket_button():
    """Тест inline кнопки добавления билета"""
    kb = add_ticket_button()
    assert len(kb.inline_keyboard) == 1
    assert len(kb.inline_keyboard[0]) == 1

    button = kb.inline_keyboard[0][0]
    assert button.text == "➕ Добавить билет"
    assert button.callback_data == "ticket_add"


def test_tickets_numbers_kb():
    """Тест inline клавиатуры с номерами билетов"""

    # Тест с 3 билетами
    kb = tickets_numbers_kb(3)
    assert len(kb.inline_keyboard) == 1
    assert len(kb.inline_keyboard[0]) == 3

    for i in range(3):
        assert kb.inline_keyboard[0][i].text == str(i + 1)
        assert kb.inline_keyboard[0][i].callback_data == f"ticket_{i + 1}"

    # Тест с 7 билетами (должно быть 2 строки: 5 + 2)
    kb = tickets_numbers_kb(7)
    assert len(kb.inline_keyboard) == 2
    assert len(kb.inline_keyboard[0]) == 5  # Первая строка: 5 кнопок
    assert len(kb.inline_keyboard[1]) == 2  # Вторая строка: 2 кнопки

    # Тест с 10 билетами (2 строки по 5)
    kb = tickets_numbers_kb(10)
    assert len(kb.inline_keyboard) == 2
    assert len(kb.inline_keyboard[0]) == 5
    assert len(kb.inline_keyboard[1]) == 5

    # Тест с 0 билетами
    kb = tickets_numbers_kb(0)
    assert len(kb.inline_keyboard) == 0  # Пустая клавиатура


def test_delete_ticket_kb():
    """Тест inline кнопки удаления билета"""
    kb = delete_ticket_kb(123)
    assert len(kb.inline_keyboard) == 1
    assert len(kb.inline_keyboard[0]) == 1

    button = kb.inline_keyboard[0][0]
    assert button.text == "🗑 Удалить этот билет"
    assert button.callback_data == "delete_123"


def test_tracked_add_button():
    """Тест inline кнопки добавления в отслеживаемые"""
    kb = tracked_add_button()
    assert len(kb.inline_keyboard) == 1
    assert len(kb.inline_keyboard[0]) == 1

    button = kb.inline_keyboard[0][0]
    assert button.text == "➕ Добавить в отслеживаемые"
    assert button.callback_data == "track_add"


def test_tracked_ticket_numbers():
    """Тест inline клавиатуры с номерами отслеживаемых билетов"""

    # Тест с 1 билетом
    kb = tracked_ticket_numbers(1)
    assert len(kb.inline_keyboard) == 1
    assert len(kb.inline_keyboard[0]) == 1
    assert kb.inline_keyboard[0][0].callback_data == "track_1"

    # Тест с 5 билетами (1 строка из 5 кнопок)
    kb = tracked_ticket_numbers(5)
    assert len(kb.inline_keyboard) == 1
    assert len(kb.inline_keyboard[0]) == 5

    # Тест с 6 билетами (2 строки: 5 + 1)
    kb = tracked_ticket_numbers(6)
    assert len(kb.inline_keyboard) == 2
    assert len(kb.inline_keyboard[0]) == 5
    assert len(kb.inline_keyboard[1]) == 1

    # Тест с 0 билетами
    kb = tracked_ticket_numbers(0)
    assert len(kb.inline_keyboard) == 0


def test_tracked_delete_kb():
    """Тест inline кнопки удаления из отслеживаемых"""
    kb = tracked_delete_kb(456)
    assert len(kb.inline_keyboard) == 1
    assert len(kb.inline_keyboard[0]) == 1

    button = kb.inline_keyboard[0][0]
    assert button.text == "Удалить из отслеживаемых"
    assert button.callback_data == "track_delete_456"


@pytest.mark.parametrize("count,expected_rows", [
    (0, 0),  # Нет билетов
    (1, 1),  # 1 строка, 1 кнопка
    (5, 1),  # 1 строка, 5 кнопок
    (6, 2),  # 2 строки: 5 + 1
    (10, 2),  # 2 строки: 5 + 5
    (11, 3),  # 3 строки: 5 + 5 + 1
    (15, 3),  # 3 строки: 5 + 5 + 5
])
def test_tickets_numbers_kb_parametrized(count, expected_rows):
    """Параметризованный тест для tickets_numbers_kb"""
    kb = tickets_numbers_kb(count)

    # Проверяем количество строк
    assert len(kb.inline_keyboard) == expected_rows

    # Проверяем общее количество кнопок
    total_buttons = sum(len(row) for row in kb.inline_keyboard)
    assert total_buttons == min(count, count)  # Все кнопки должны быть

    # Проверяем текст и callback_data кнопок
    button_num = 1
    for row in kb.inline_keyboard:
        for button in row:
            assert button.text == str(button_num)
            assert button.callback_data == f"ticket_{button_num}"
            button_num += 1


@pytest.mark.parametrize("field", ["багаж", "пересадки", "цена", "место вылета"])
def test_filters_delete_kb_parametrized(field):
    """Параметризованный тест для filters_delete_kb с разными полями"""
    kb = filters_delete_kb(field)

    assert len(kb.keyboard) == 2
    assert kb.keyboard[0][0].text == f"Удалить фильтр ({field})"
    assert kb.keyboard[1][0].text == "⬅️ Назад в меню"


def test_tickets_numbers_kb_large_count():
    """Тест с большим количеством билетов"""
    kb = tickets_numbers_kb(25)  # 5 строк по 5 кнопок
    assert len(kb.inline_keyboard) == 5

    # Проверяем последнюю кнопку
    last_row = kb.inline_keyboard[-1]
    last_button = last_row[-1]
    assert last_button.text == "25"
    assert last_button.callback_data == "ticket_25"


def test_tracked_ticket_numbers_edge_cases():
    """Тест граничных случаев для tracked_ticket_numbers"""

    # Отрицательное число (должно обрабатываться корректно)
    kb = tracked_ticket_numbers(-1)
    assert len(kb.inline_keyboard) == 0

    # Большое число
    kb = tracked_ticket_numbers(100)
    # Должно быть 20 строк по 5 кнопок
    assert len(kb.inline_keyboard) == 20

    # Проверяем последнюю кнопку
    last_button = kb.inline_keyboard[-1][-1]
    assert last_button.text == "100"
    assert last_button.callback_data == "track_100"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])