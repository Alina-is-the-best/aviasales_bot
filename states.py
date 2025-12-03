from aiogram.fsm.state import StatesGroup, State


class SimpleSearch(StatesGroup):
    # Одна сторона
    from_city = State()
    to_city = State()
    trip_type = State()

    # Даты
    dates = State()  # для one-way (одна дата)

    # Для туда-обратно:
    depart_date = State()  # дата вылета
    return_date = State()  # дата возвращения

    # Остальное
    baggage = State()
    transfers = State()
    price_limit = State()


class ComplexSearch(StatesGroup):
    segment_from = State()
    segment_to = State()
    segment_date = State()
    add_segment = State()

    baggage = State()
    transfers = State()
    price_limit = State()

class HotTickets(StatesGroup):
    from_city = State()


class ComplexSearch(StatesGroup):
    segments = State()  # список сегментов
    segment_from = State()  # откуда
    segment_to = State()  # куда
    segment_date = State()  # дата сегмента
    add_more = State()  # спрашиваем: добавить сегмент?

    baggage = State()
    transfers = State()
    price_limit = State()


class TicketAdd(StatesGroup):
    waiting_for_data = State()

class UserFiltersState(StatesGroup):
    from_city = State()
    baggage = State()
    transfers = State()
    price_limit = State()
