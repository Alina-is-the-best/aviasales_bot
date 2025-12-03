from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
import keyboards
from states import UserFiltersState
import filters_repository as filters_repo

router = Router()

def register(dp):
    dp.include_router(router)


# -----------------------------------------------------
# ГЛАВНОЕ МЕНЮ НАСТРОЕК
# -----------------------------------------------------
@router.message(F.text == "Настройки")
async def settings_root(msg: types.Message):
    await msg.answer(
        "Раздел настроек:",
        reply_markup=keyboards.settings_menu()
    )


# -----------------------------------------------------
# ВАЛЮТА
# -----------------------------------------------------
@router.message(F.text == "Валюта")
async def currency_setting(msg: types.Message):
    await msg.answer(
        "Эта функция скоро будет реализована 💱",
        reply_markup=keyboards.settings_menu()
    )


# -----------------------------------------------------
# УВЕДОМЛЕНИЯ
# -----------------------------------------------------
@router.message(F.text == "Уведомления")
async def notifications_setting(msg: types.Message):
    await msg.answer(
        "Функция уведомлений скоро появится 🔔",
        reply_markup=keyboards.settings_menu()
    )


# -----------------------------------------------------
# ПОСТОЯННЫЕ ФИЛЬТРЫ
# -----------------------------------------------------
@router.message(F.text == "Постоянные фильтры")
async def filters_root(msg: types.Message):
    await msg.answer(
        "Выберите фильтр:",
        reply_markup=keyboards.filters_menu()
    )


# -----------------------------------------------------
# МЕСТО ВЫЛЕТА
# -----------------------------------------------------
@router.message(F.text == "Место вылета ✈️")
async def filter_from_city(msg: types.Message, state: FSMContext):
    await state.set_state(UserFiltersState.from_city)
    await msg.answer(
        "Введите город, который будет использоваться как постоянный фильтр:",
        reply_markup=keyboards.filters_delete_kb("место вылета")
    )


@router.message(UserFiltersState.from_city)
async def save_from_city(msg: types.Message, state: FSMContext):
    if msg.text.startswith("Удалить фильтр"):
        await filters_repo.clear_filter(msg.from_user.id, "from_city")
        await state.clear()
        return await msg.answer("Фильтр удалён.", reply_markup=keyboards.filters_menu())

    await filters_repo.update_filter(msg.from_user.id, "from_city", msg.text)
    await state.clear()
    await msg.answer("Фильтр сохранён.", reply_markup=keyboards.filters_menu())


# -----------------------------------------------------
# БАГАЖ (кнопочный выбор)
# -----------------------------------------------------
@router.message(F.text == "Багаж 🎒")
async def filter_baggage(msg: types.Message, state: FSMContext):
    await state.set_state(UserFiltersState.baggage)
    await msg.answer(
        "Выберите тип багажа:",
        reply_markup=keyboards.filter_baggage_kb()
    )


@router.message(UserFiltersState.baggage)
async def save_baggage(msg: types.Message, state: FSMContext):
    text = msg.text

    if text == "⬅️ Назад в меню":
        await state.clear()
        return await msg.answer("Главное меню:", reply_markup=keyboards.settings_menu())

    if text == "Удалить фильтр (багаж)":
        await filters_repo.clear_filter(msg.from_user.id, "baggage")
        await state.clear()
        return await msg.answer("Фильтр багаж удалён.", reply_markup=keyboards.filters_menu())

    if text not in ["С багажом", "Без багажа"]:
        return await msg.answer("Выберите вариант с кнопок.")

    await filters_repo.update_filter(msg.from_user.id, "baggage", text)
    await state.clear()
    await msg.answer("Фильтр багаж сохранён.", reply_markup=keyboards.filters_menu())


# -----------------------------------------------------
# ПЕРЕСАДКИ (кнопочный выбор)
# -----------------------------------------------------
@router.message(F.text == "Пересадки ↩️")
async def filter_transfers(msg: types.Message, state: FSMContext):
    await state.set_state(UserFiltersState.transfers)
    await msg.answer(
        "Выберите тип пересадок:",
        reply_markup=keyboards.filter_transfers_kb()
    )


@router.message(UserFiltersState.transfers)
async def save_transfers(msg: types.Message, state: FSMContext):
    text = msg.text

    if text == "⬅️ Назад в меню":
        await state.clear()
        return await msg.answer("Главное меню:", reply_markup=keyboards.settings_menu())

    if text == "Удалить фильтр (пересадки)":
        await filters_repo.clear_filter(msg.from_user.id, "transfers")
        await state.clear()
        return await msg.answer("Фильтр пересадок удалён.", reply_markup=keyboards.filters_menu())

    if text not in ["Только прямой рейс", "Любые пересадки"]:
        return await msg.answer("Выберите вариант с кнопок.")

    await filters_repo.update_filter(msg.from_user.id, "transfers", text)
    await state.clear()
    await msg.answer("Фильтр пересадок сохранён.", reply_markup=keyboards.filters_menu())


# -----------------------------------------------------
# ЦЕНОВОЕ ОГРАНИЧЕНИЕ
# -----------------------------------------------------
@router.message(F.text == "Ценовые ограничения 💴")
async def filter_price(msg: types.Message, state: FSMContext):
    await state.set_state(UserFiltersState.price_limit)
    await msg.answer(
        "Введите максимальную цену:",
        reply_markup=keyboards.filters_delete_kb("ценовой фильтр")
    )


@router.message(UserFiltersState.price_limit)
async def save_price(msg: types.Message, state: FSMContext):
    if msg.text.startswith("Удалить фильтр"):
        await filters_repo.clear_filter(msg.from_user.id, "price_limit")
        await state.clear()
        return await msg.answer("Фильтр удалён.", reply_markup=keyboards.filters_menu())

    await filters_repo.update_filter(msg.from_user.id, "price_limit", msg.text)
    await state.clear()
    await msg.answer("Фильтр сохранён.", reply_markup=keyboards.filters_menu())

