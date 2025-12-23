from datetime import datetime, timedelta

def is_date_in_coming_week(date_str: str) -> bool:
    if not date_str: return False
    try:
        # Убираем время, оставляем только дату 2025-12-23
        flight_date = datetime.fromisoformat(date_str.replace('Z', '')).date()
        today = datetime.now().date()
        margin = today + timedelta(days=7)
        
        # Если дата билета сегодня или в течение 7 дней
        return today <= flight_date <= margin
    except:
        return False

def format_date_for_api(date_str: str) -> str:
    """Преобразует 01.01.2025 -> 2025-01-01"""
    if not date_str: return None
    try:
        day, month, year = date_str.split('.')
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    except ValueError:
        return None

def format_date_for_user(iso_date: str) -> str:
    """Преобразует 2025-01-01... -> 01.01.2025 15:30"""
    if not iso_date: return "?"
    try:
        # Убираем Z и миллисекунды, если есть
        iso_date = iso_date.replace('Z', '')
        if 'T' in iso_date:
            dt = datetime.fromisoformat(iso_date)
            return dt.strftime("%d.%m.%Y %H:%M")
        else:
            dt = datetime.strptime(iso_date, "%Y-%m-%d")
            return dt.strftime("%d.%m.%Y")
    except Exception:
        return iso_date

def get_transfers_text(count: int) -> str:
    if count == 0: return "прямой"
    if count == 1: return "1 пересадка"
    return f"{count} пересадки"

def format_one_way_ticket(flight: dict, origin: str, dest: str, index: int = None) -> str:
    """Создает красивый текст для одного билета"""
    price = flight.get('price', flight.get('value', 0))
    airline = flight.get('airline', flight.get('airline_iata', 'Aviasales'))
    
    dep_at = format_date_for_user(flight.get('departure_at'))
    
    transfers = flight.get('transfers', flight.get('number_of_changes', 0))
    transfers_text = get_transfers_text(transfers)
    prefix = f"{index}. " if index else ""

    return (
        f"{prefix}✈️ **{airline}**\n"
        f"📍 {origin} → {dest}\n"
        f"📅 {dep_at} ({transfers_text})\n"
        f"💰 **{price}₽**\n"
    )

def format_round_trip_ticket(ft: dict, fb: dict, origin: str, dest: str, index: int = None) -> str:
    """Создает красивый текст для билета туда-обратно"""
    total_price = ft.get('price', 0) + fb.get('price', 0)
    
    dep_there = format_date_for_user(ft.get('departure_at'))
    dep_back = format_date_for_user(fb.get('departure_at'))
    
    tr_there = get_transfers_text(ft.get('transfers', 0))
    tr_back = get_transfers_text(fb.get('transfers', 0))
    
    prefix = f"{index}. " if index else ""

    return (
        f"{prefix}✈️ **Туда-обратно**\n"
        f"📍 {origin} ↔ {dest}\n"
        f"💰 **Всего: {total_price}₽**\n"
        f"🛫 Туда: {dep_there} ({tr_there})\n"
        f"🛬 Обратно: {dep_back} ({tr_back})\n"
    )