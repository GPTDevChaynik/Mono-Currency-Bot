from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.button(text="💰 Курси валют", callback_data="rates")
    kb.button(text="💳 Конвертер", callback_data="converter")
    kb.button(text="ℹ️ Як працює конвертація", callback_data="about")

    kb.adjust(1)

    return kb.as_markup()


def rates_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Оновити", callback_data="rates")
    kb.button(text="🏠 Головне меню", callback_data="home")
    kb.adjust(1)
    return kb.as_markup()


def home_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 Головне меню", callback_data="home")
    kb.adjust(1)
    return kb.as_markup()


def currency_menu(prefix: str, currencies: tuple[str, ...]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for currency in currencies:
        kb.button(text=currency_label(currency), callback_data=f"{prefix}:{currency}")

    kb.button(text="🏠 Головне меню", callback_data="home")

    kb.adjust(3)

    return kb.as_markup()


def result_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.button(text="🔄 Новий розрахунок", callback_data="converter")
    kb.button(text="🏠 Головне меню", callback_data="home")

    kb.adjust(1)

    return kb.as_markup()


def currency_label(currency: str) -> str:
    flags = {
        "UAH": "🇺🇦",
        "USD": "🇺🇸",
        "EUR": "🇪🇺",
        "PLN": "🇵🇱",
        "GEL": "🇬🇪",
        "GBP": "🇬🇧",
        "CHF": "🇨🇭",
        "CZK": "🇨🇿",
        "TRY": "🇹🇷",
        "HUF": "🇭🇺",
        "CAD": "🇨🇦",
        "AUD": "🇦🇺",
        "SEK": "🇸🇪",
        "NOK": "🇳🇴",
        "DKK": "🇩🇰",
        "JPY": "🇯🇵",
        "CNY": "🇨🇳",
    }
    return f"{flags.get(currency, '')} {currency}".strip()
