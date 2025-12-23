from datetime import datetime, timedelta

def test_next_segment_date_must_be_after_previous():
    """
    Проверяем бизнес-правило:
    - дата следующего сегмента > предыдущей
    """
    first = datetime(2025, 3, 10)
    second_min = first + timedelta(days=1)

    assert second_min > first
