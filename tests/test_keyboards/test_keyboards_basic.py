from infra.keyboards.keyboards import main_menu, back_to_main

def test_main_menu_returns_markup():
    kb = main_menu()
    assert kb is not None

def test_back_to_main_returns_markup():
    kb = back_to_main()
    assert kb is not None
