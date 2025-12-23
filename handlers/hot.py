from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from keyboards import keyboards
from states import HotTickets

from parser.aviasales_api import parse_flights
from data.city_codes import get_city_code

router = Router()

def register(dp):
    dp.include_router(router)


# выбираем город
@router.message(F.text == "Горячие билеты")
async def hot_start(msg: types.Message, state: FSMContext):
    await state.set_state(HotTickets.from_city)
    await msg.answer(
        "Откуда летим?",
        reply_markup=keyboards.back_to_main()
    )


# ловим введённый город
@router.message(HotTickets.from_city)
async def hot_city_received(msg: types.Message, state: FSMContext):
    if msg.text == "⬅️ Назад в меню":
        await state.clear()
        return await msg.answer("Главное меню:", reply_markup=keyboards.main_menu())
    
    user_city = msg.text.strip()
    city_code = get_city_code(user_city)
    
    await msg.answer(f"Ищу горячие билеты из: {user_city} ({city_code}) 🔥")
    
    try:
        popular_destinations = ['LED', 'AER', 'KRR', 'KZN', 'SVX']  # СПб, Сочи, Краснодар, Казань, Екатеринбург
        
        response_text = f"🔥 Популярные направления из {user_city}:\n\n"
        
        for dest_code in popular_destinations[:3]:  # Проверим первые 3
            result = await parse_flights(
                origin=city_code,
                destination=dest_code,
                depart_date="2025-12-27",  # Ближайшая дата
                currency="RUB",
                endpoint="latest"
            )
            
            if result.get("data"):
                for dest, flights_dict in result["data"].items():
                    if isinstance(flights_dict, dict):
                        for flight_key, flight in flights_dict.items():
                            if isinstance(flight, dict):
                                price = flight.get('price', '?')
                                airline = flight.get('airline', '?')
                                departure = flight.get('departure_at', '?').split('T')[0] if flight.get('departure_at') else '?'
                                
                                # Получаем название города по коду
                                dest_name = dest
                                response_text += (
                                    f"• {user_city} → {dest_name}\n"
                                    f"  💰 От {price}₽\n"
                                    f"  🏢 {airline}\n"
                                    f"  📅 {departure}\n\n"
                                )
                                break  # Только первый билет
                        break
        
        await msg.answer(response_text if len(response_text) > 50 else "Горячие билеты не найдены")
        
    except Exception as e:
        await msg.answer(f"Произошла ошибка: {str(e)}")
    
    await state.clear()