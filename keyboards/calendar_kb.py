import calendar
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def build_calendar(year: int, month: int, min_date: datetime = None):
    kb = []

    # Заголовок
    kb.append([
        InlineKeyboardButton(
            text=f"{calendar.month_name[month]} {year}",
            callback_data="ignore"
        )
    ])

    # Дни недели
    week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    kb.append([InlineKeyboardButton(text=d, callback_data="ignore") for d in week_days])

    month_calendar = calendar.monthcalendar(year, month)

    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
                continue

            # дата на календаре
            current_date = datetime(year, month, day)

            # если есть минимальная дата (выбрана дата вылета)
            if min_date and current_date <= min_date:
                # эта кнопка будет неактивной
                row.append(InlineKeyboardButton(text=str(day), callback_data="ignore"))
            else:
                row.append(
                    InlineKeyboardButton(
                        text=str(day),
                        callback_data=f"date_{year}_{month}_{day}"
                    )
                )
        kb.append(row)

    # Навигация по месяцам
    prev_month = month - 1
    next_month = month + 1
    prev_year = year
    next_year = year

    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    if next_month == 13:
        next_month = 1
        next_year += 1

    kb.append([
        InlineKeyboardButton(text="⬅️", callback_data=f"prev_{prev_year}_{prev_month}"),
        InlineKeyboardButton(text="➡️", callback_data=f"next_{next_year}_{next_month}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=kb)
