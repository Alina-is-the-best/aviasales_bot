class ApiError(Exception):
    """Базовое исключение для ошибок API."""
    pass

class RateLimitError(ApiError):
    """Ошибка превышения лимита (429)."""
    pass

class ParseError(ApiError):
    """Ошибка парсинга ответа (не JSON, неожиданный формат)."""
    pass