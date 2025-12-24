from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


# Главное меню
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Горячие билеты")],
            [KeyboardButton(text="Найти билеты")],
            [KeyboardButton(text=".")],
            [KeyboardButton(text="Мои билеты")],
            [KeyboardButton(text="Настройки")],
            [KeyboardButton(text="Что я умею")],
        ],
        resize_keyboard=True
    )


# Меню выбора типа маршрута
def route_type_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Простой маршрут")],
            [KeyboardButton(text="Сложный маршрут")],
            [KeyboardButton(text="⬅️ Назад в меню")],
        ],
        resize_keyboard=True
    )


# Кнопка "Назад в меню"
def back_to_main():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Назад в меню")],
        ],
        resize_keyboard=True
    )


# Тип маршрута
def trip_type_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="В одну сторону")],
            [KeyboardButton(text="Туда-обратно")],
            [KeyboardButton(text="⬅️ Назад в меню")],
        ],
        resize_keyboard=True
    )


# Календарь выбора даты
def calendar_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Календарь")],
            [KeyboardButton(text="⬅️ Назад в меню")],
        ],
        resize_keyboard=True
    )


# Багаж
def baggage_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="С багажом")],
            [KeyboardButton(text="Без багажа")],
            [KeyboardButton(text="⬅️ Назад в меню")],
        ],
        resize_keyboard=True
    )


# Пересадки
def transfers_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Только прямой")],
            [KeyboardButton(text="Любой подойдет")],
            [KeyboardButton(text="⬅️ Назад в меню")],
        ],
        resize_keyboard=True
    )

def complex_add_more_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить сегмент")],
            [KeyboardButton(text="✔ Завершить маршрут")],
            [KeyboardButton(text="⬅️ Назад в меню")]
        ],
        resize_keyboard=True
    )


def tickets_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Купленные билеты")],
            [KeyboardButton(text="Отслеживаемые билеты")],
            [KeyboardButton(text="⬅️ Назад в меню")],
        ],
        resize_keyboard=True
    )


def add_ticket_button():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить билет", callback_data="ticket_add")]
        ]
    )


def tickets_numbers_kb(ticket_count: int):
    row = []
    buttons = []

    for i in range(1, ticket_count + 1):
        buttons.append(InlineKeyboardButton(text=str(i), callback_data=f"ticket_{i}"))

        if len(buttons) == 5:
            row.append(buttons)
            buttons = []

    if buttons:
        row.append(buttons)

    return InlineKeyboardMarkup(inline_keyboard=row)


def delete_ticket_kb(ticket_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Удалить этот билет", callback_data=f"delete_{ticket_id}")]
        ]
    )

def tracked_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Купленные билеты")],
            [KeyboardButton(text="Отслеживаемые билеты")],
            [KeyboardButton(text="⬅️ Назад в меню")]
        ],
        resize_keyboard=True
    )


def tracked_add_button():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить в отслеживаемые", callback_data="track_add")]
        ]
    )


def tracked_ticket_numbers(count: int):
    rows = []
    row = []
    for i in range(1, count + 1):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"track_{i}"))
        if len(row) == 5:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def tracked_delete_kb(ticket_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Удалить из отслеживаемых", callback_data=f"track_delete_{ticket_id}")]
        ]
    )

def settings_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Валюта")],
            [KeyboardButton(text="Уведомления")],
            [KeyboardButton(text="Постоянные фильтры")],
            [KeyboardButton(text="⬅️ Назад в меню")]
        ],
        resize_keyboard=True
    )


def filters_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Место вылета ✈️")],
            [KeyboardButton(text="Багаж 🎒")],
            [KeyboardButton(text="Пересадки ↩️")],
            [KeyboardButton(text="Ценовые ограничения 💴")],
            [KeyboardButton(text="⬅️ Назад в меню")]
        ],
        resize_keyboard=True
    )


def filters_delete_kb(field: str):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"Удалить фильтр ({field})")],
            [KeyboardButton(text="⬅️ Назад в меню")]
        ],
        resize_keyboard=True
    )

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def filter_baggage_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="С багажом"), KeyboardButton(text="Без багажа")],
            [KeyboardButton(text="Удалить фильтр (багаж)")],
            [KeyboardButton(text="⬅️ Назад в меню")]
        ],
        resize_keyboard=True
    )


def filter_transfers_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Только прямой рейс")],
            [KeyboardButton(text="Любые пересадки")],
            [KeyboardButton(text="Удалить фильтр (пересадки)")],
            [KeyboardButton(text="⬅️ Назад в меню")]
        ],
        resize_keyboard=True
    )

def hot_dest_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌍 Куда угодно")],
            [KeyboardButton(text="⬅️ Назад в меню")]
        ],
        resize_keyboard=True
    )