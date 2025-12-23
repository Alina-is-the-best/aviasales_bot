from keyboards.keyboards import (
    main_menu,
    route_type_menu,
    baggage_kb,
    transfers_kb
)

def test_main_menu_buttons():
    kb = main_menu()
    assert len(kb.keyboard) > 0


def test_route_type_menu():
    kb = route_type_menu()

    # 3 строки: простой, сложный, назад
    assert len(kb.keyboard) == 3

    assert kb.keyboard[0][0].text == "Простой маршрут"
    assert kb.keyboard[1][0].text == "Сложный маршрут"
    assert kb.keyboard[2][0].text == "⬅️ Назад в меню"



def test_baggage_kb():
    kb = baggage_kb()
    texts = [btn.text for row in kb.keyboard for btn in row]
    assert "С багажом" in texts


def test_transfers_kb():
    kb = transfers_kb()
    assert kb.keyboard
