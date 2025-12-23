from datetime import datetime
from keyboards.calendar_kb import build_calendar

def test_calendar_returns_inline_keyboard():
    """
    Проверяем:
    - build_calendar возвращает InlineKeyboardMarkup
    """
    kb = build_calendar(2025, 3)

    assert kb is not None
    assert len(kb.inline_keyboard) > 0

def test_calendar_blocks_past_dates():
    """
    Проверяем:
    - даты <= min_date не кликабельны
    """
    min_date = datetime(2025, 3, 10)
    kb = build_calendar(2025, 3, min_date=min_date)

    # ищем кнопку "9"
    all_buttons = [
        btn for row in kb.inline_keyboard for btn in row
    ]

    blocked = [
        btn for btn in all_buttons
        if btn.text == "9" and btn.callback_data == "ignore"
    ]

    assert blocked, "Дата до min_date должна быть заблокирована"
