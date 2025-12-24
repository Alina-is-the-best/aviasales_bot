import pytest
import sys
from unittest.mock import AsyncMock, patch, MagicMock

# Мокаем проблемные модули ПЕРЕД импортом
sys.modules['adapters.api.aviasales_api'] = MagicMock()
sys.modules['infra.config'] = MagicMock()
sys.modules['commands.search'] = MagicMock()

# Теперь безопасно импортируем hot
from infra.handlers import hot


class DummyState:
    def __init__(self):
        self.cleared = False
        self._data = {}
        self.current_state = None

    async def clear(self):
        self.cleared = True
        self._data = {}
        self.current_state = None

    async def set_state(self, state):
        self.current_state = state

    async def update_data(self, **kwargs):
        self._data.update(kwargs)

    async def get_data(self):
        return self._data.copy()


class DummyMsg:
    def __init__(self, text="Москва"):
        self.text = text
        self.answers = []
        self.reply_markups = []
        self.parse_modes = []
        self.web_page_preview_settings = []

    async def answer(self, text, reply_markup=None, parse_mode=None, disable_web_page_preview=None):
        self.answers.append(text)
        if reply_markup:
            self.reply_markups.append(reply_markup)
        self.parse_modes.append(parse_mode)  # Всегда добавляем, даже если None
        self.web_page_preview_settings.append(disable_web_page_preview)  # Всегда добавляем


@pytest.mark.asyncio
async def test_hot_start_handler():
    """Тест начала диалога горячих билетов"""
    msg = DummyMsg("Горячие билеты")
    state = DummyState()

    # Мокаем reply_markup
    mock_keyboard = MagicMock()
    with patch('infra.handlers.hot.keyboards') as mock_keyboards:
        mock_keyboards.back_to_main.return_value = mock_keyboard

        await hot.hot_start(msg, state)

        assert state.current_state == hot.HotTickets.from_city
        assert "🔥 Откуда летим?" in msg.answers[0]
        assert len(msg.answers) == 1


@pytest.mark.asyncio
async def test_hot_from_city_valid():
    """Тест обработки валидного города отправления"""
    msg = DummyMsg("Москва")
    state = DummyState()

    # Мокаем все зависимости
    with patch('infra.handlers.hot.get_city_code', return_value='MOW'):
        with patch('infra.handlers.hot.keyboards') as mock_keyboards:
            mock_keyboards.hot_dest_kb.return_value = MagicMock()

            await hot.hot_from_city(msg, state)

            data = await state.get_data()
            assert data['from_city'] == "Москва"
            assert data['from_code'] == "MOW"
            assert state.current_state == hot.HotTickets.to_city
            assert f"Куда летим из Москва?" in msg.answers[0]


@pytest.mark.asyncio
async def test_hot_from_city_invalid():
    """Тест обработки невалидного города"""
    msg = DummyMsg("Несуществующий город")
    state = DummyState()

    with patch('infra.handlers.hot.get_city_code', return_value=None):
        await hot.hot_from_city(msg, state)

        assert "❌ Город не найден" in msg.answers[0]


@pytest.mark.asyncio
async def test_hot_from_city_back():
    """Тест возврата в меню"""
    msg = DummyMsg("⬅️ Назад в меню")
    state = DummyState()

    with patch('infra.handlers.hot.keyboards') as mock_keyboards:
        mock_keyboards.main_menu.return_value = MagicMock()

        await hot.hot_from_city(msg, state)

        assert state.cleared == True
        assert "Главное меню:" in msg.answers[0]


@pytest.mark.asyncio
async def test_hot_finish_to_city():
    """Тест поиска билетов в конкретный город"""
    msg = DummyMsg("Санкт-Петербург")
    state = DummyState()
    state._data = {'from_city': 'Москва', 'from_code': 'MOW'}

    # Мокаем все зависимости
    with patch('infra.handlers.hot.get_city_code', return_value='LED'):
        with patch('infra.handlers.hot.parse_flights', new_callable=AsyncMock) as mock_parse:
            with patch('infra.handlers.hot.is_date_in_coming_week', return_value=True):
                with patch('infra.handlers.hot.format_one_way_ticket',
                           return_value="✅ Билет найден"):
                    # Мокаем успешный ответ API
                    mock_parse.return_value = {
                        'data': [{
                            'price': 5000,
                            'airline': 'SU',
                            'flight_number': '123',
                            'departure_at': '2024-01-01T10:00:00Z',
                            'destination': 'LED',
                            'link': 'https://example.com'
                        }]
                    }

                    await hot.hot_finish(msg, state)

                    assert "🔎 Ищу билеты в Санкт-Петербург" in msg.answers[0]
                    assert "🔥 **Самый горячий билет:**" in msg.answers[1]
                    # Проверяем, что parse_mode был установлен во втором сообщении
                    assert len(msg.parse_modes) >= 2
                    assert msg.parse_modes[1] == "Markdown"
                    assert msg.web_page_preview_settings[1] == True
                    assert state.cleared == True


@pytest.mark.asyncio
async def test_hot_finish_to_city_no_tickets():
    """Тест поиска билетов, когда билетов нет"""
    msg = DummyMsg("Санкт-Петербург")
    state = DummyState()
    state._data = {'from_city': 'Москва', 'from_code': 'MOW'}

    with patch('infra.handlers.hot.get_city_code', return_value='LED'):
        with patch('infra.handlers.hot.parse_flights', new_callable=AsyncMock) as mock_parse:
            # Мокаем пустой ответ API
            mock_parse.return_value = {'data': []}

            await hot.hot_finish(msg, state)

            assert "🔎 Ищу билеты в Санкт-Петербург" in msg.answers[0]
            assert "😔 Билетов не найдено." in msg.answers[1]


@pytest.mark.asyncio
async def test_hot_finish_to_city_no_flights_this_week():
    """Тест, когда нет билетов на этой неделе, но есть на другие даты"""
    msg = DummyMsg("Санкт-Петербург")
    state = DummyState()
    state._data = {'from_city': 'Москва', 'from_code': 'MOW'}

    with patch('infra.handlers.hot.get_city_code', return_value='LED'):
        with patch('infra.handlers.hot.parse_flights', new_callable=AsyncMock) as mock_parse:
            with patch('infra.handlers.hot.is_date_in_coming_week', return_value=False):
                with patch('infra.handlers.hot.format_one_way_ticket',
                           return_value="✅ Билет на другую дату"):
                    # Мокаем билеты, но не на эту неделю
                    mock_parse.return_value = {
                        'data': [{
                            'price': 5000,
                            'airline': 'SU',
                            'flight_number': '123',
                            'departure_at': '2024-02-01T10:00:00Z',
                            'destination': 'LED',
                            'link': 'https://example.com'
                        }]
                    }

                    await hot.hot_finish(msg, state)

                    assert "🔎 Ищу билеты в Санкт-Петербург" in msg.answers[0]
                    assert "⏳ На этой неделе билетов нет" in msg.answers[1]


@pytest.mark.asyncio
async def test_hot_finish_anywhere():
    """Тест режима 'Куда угодно'"""
    msg = DummyMsg("🌍 Куда угодно")
    state = DummyState()
    state._data = {'from_city': 'Москва', 'from_code': 'MOW'}

    # Мокаем asyncio.gather
    mock_flight_data = [{
        'price': 4000,
        'departure_at': '2024-01-01T10:00:00Z',
        'destination': 'LED',
        'airline': 'SU',
        'flight_number': '123',
        'link': 'https://example.com'
    }]

    with patch('infra.handlers.hot.asyncio.gather', new_callable=AsyncMock) as mock_gather:
        with patch('infra.handlers.hot.parse_flights', new_callable=AsyncMock):
            with patch('infra.handlers.hot.is_date_in_coming_week', return_value=True):
                with patch('infra.handlers.hot.format_one_way_ticket',
                           return_value="1. Направление\n"):
                    # Мокаем результаты поиска
                    mock_gather.return_value = [
                        {'data': mock_flight_data},
                        {'data': []},
                        {'data': []},
                        {'data': []},
                        {'data': []},
                        {'data': []},
                        {'data': []}
                    ]

                    await hot.hot_finish(msg, state)

                    assert "🔎 Ищу лучшие варианты" in msg.answers[0]
                    assert "🌍 **Топ выгодных направлений:**" in msg.answers[1]
                    # Проверяем, что parse_mode был установлен
                    assert len(msg.parse_modes) >= 2
                    assert msg.parse_modes[1] == "Markdown"
                    assert msg.web_page_preview_settings[1] == True
                    assert state.cleared == True


@pytest.mark.asyncio
async def test_hot_finish_anywhere_no_results():
    """Тест режима 'Куда угодно', когда нет результатов"""
    msg = DummyMsg("🌍 Куда угодно")
    state = DummyState()
    state._data = {'from_city': 'Москва', 'from_code': 'MOW'}

    with patch('infra.handlers.hot.asyncio.gather', new_callable=AsyncMock) as mock_gather:
        with patch('infra.handlers.hot.parse_flights', new_callable=AsyncMock):
            # Все запросы возвращают пустые данные
            mock_gather.return_value = [
                {'data': []},
                {'data': []},
                {'data': []},
                {'data': []},
                {'data': []},
                {'data': []},
                {'data': []}
            ]

            await hot.hot_finish(msg, state)

            assert "🔎 Ищу лучшие варианты" in msg.answers[0]
            assert "😔 На ближайшую неделю билетов 'куда угодно' не нашлось." in msg.answers[1]


@pytest.mark.asyncio
async def test_hot_finish_back_to_menu():
    """Тест возврата в меню из состояния выбора города назначения"""
    msg = DummyMsg("⬅️ Назад в меню")
    state = DummyState()
    state._data = {'from_city': 'Москва', 'from_code': 'MOW'}

    with patch('infra.handlers.hot.keyboards') as mock_keyboards:
        mock_keyboards.main_menu.return_value = MagicMock()

        await hot.hot_finish(msg, state)

        assert state.cleared == True
        assert "Вы вернулись в главное меню" in msg.answers[0]


@pytest.mark.asyncio
async def test_hot_finish_invalid_destination():
    """Тест невалидного города назначения"""
    msg = DummyMsg("Несуществующий город")
    state = DummyState()
    state._data = {'from_city': 'Москва', 'from_code': 'MOW'}

    with patch('infra.handlers.hot.get_city_code', return_value=None):
        await hot.hot_finish(msg, state)

        assert "❌ Город не найден" in msg.answers[0]


if __name__ == "__main__":
    # Для запуска теста напрямую
    pytest.main([__file__, "-v"])