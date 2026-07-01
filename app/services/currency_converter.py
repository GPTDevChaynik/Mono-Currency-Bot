from dataclasses import dataclass

from app.services.monobank import MonoRates


VISA_CALCULATOR_URL = "https://www.visa.com.ua/en_UA/support/consumer/travel-support/exchange-rate-calculator.html"
MASTERCARD_CALCULATOR_URL = "https://www.mastercard.com/ua/uk/personal/get-support/currency-exchange-rate-converter.html"

CARD_CURRENCIES = ("UAH", "USD", "EUR")
PURCHASE_CURRENCIES = (
    "UAH",
    "USD",
    "EUR",
    "PLN",
    "GEL",
    "GBP",
    "CHF",
    "CZK",
    "TRY",
    "HUF",
    "CAD",
    "AUD",
    "SEK",
    "NOK",
    "DKK",
    "JPY",
    "CNY",
)


@dataclass(frozen=True)
class ConversionResult:
    debit_amount: float | None
    card_currency: str
    purchase_amount: float
    purchase_currency: str
    explanation: str
    assumption: str | None = None
    is_estimate: bool = False


def convert_purchase(
    amount: float,
    card_currency: str,
    purchase_currency: str,
    rates: MonoRates,
) -> ConversionResult:
    if card_currency == purchase_currency:
        return ConversionResult(
            debit_amount=amount,
            card_currency=card_currency,
            purchase_amount=amount,
            purchase_currency=purchase_currency,
            explanation="Валюта картки збігається з валютою покупки, тому конвертація не потрібна.",
        )

    if card_currency not in CARD_CURRENCIES:
        return _payment_system_result(amount, card_currency, purchase_currency)

    if card_currency == "UAH":
        return _to_uah_card(amount, purchase_currency, rates)

    if card_currency == "USD":
        return _to_usd_card(amount, purchase_currency, rates)

    return _to_eur_card(amount, purchase_currency, rates)


def _to_uah_card(amount: float, purchase_currency: str, rates: MonoRates) -> ConversionResult:
    if purchase_currency in {"USD", "EUR"}:
        rate = rates.rate_to_uah(purchase_currency, "sell")
        return ConversionResult(
            debit_amount=amount * rate if rate else None,
            card_currency="UAH",
            purchase_amount=amount,
            purchase_currency=purchase_currency,
            explanation=f"{purchase_currency} конвертується в UAH за курсом продажу Monobank.",
        )

    return _payment_system_estimate(amount, "UAH", purchase_currency, rates)


def _to_usd_card(amount: float, purchase_currency: str, rates: MonoRates) -> ConversionResult:
    if purchase_currency == "UAH":
        rate = rates.rate_to_uah("USD", "buy")
        return ConversionResult(
            debit_amount=amount / rate if rate else None,
            card_currency="USD",
            purchase_amount=amount,
            purchase_currency="UAH",
            explanation="UAH конвертується в USD за курсом купівлі Monobank.",
        )

    if purchase_currency == "EUR":
        debit = _safe_cross(amount, "EUR", "USD", rates)
        return ConversionResult(
            debit_amount=debit,
            card_currency="USD",
            purchase_amount=amount,
            purchase_currency="EUR",
            explanation="EUR конвертується в USD за курсом продажу Monobank.",
            assumption=rates.cross_assumption("EUR", "USD"),
        )

    return _payment_system_estimate(amount, "USD", purchase_currency, rates)


def _to_eur_card(amount: float, purchase_currency: str, rates: MonoRates) -> ConversionResult:
    if purchase_currency == "UAH":
        rate = rates.rate_to_uah("EUR", "buy")
        return ConversionResult(
            debit_amount=amount / rate if rate else None,
            card_currency="EUR",
            purchase_amount=amount,
            purchase_currency="UAH",
            explanation="UAH конвертується в EUR за курсом купівлі Monobank.",
        )

    if purchase_currency == "USD":
        debit = _safe_cross(amount, "USD", "EUR", rates)
        return ConversionResult(
            debit_amount=debit,
            card_currency="EUR",
            purchase_amount=amount,
            purchase_currency="USD",
            explanation="USD конвертується в EUR за курсом продажу Monobank.",
            assumption=rates.cross_assumption("USD", "EUR"),
        )

    return _payment_system_estimate(amount, "EUR", purchase_currency, rates)


def _payment_system_estimate(
    amount: float,
    card_currency: str,
    purchase_currency: str,
    rates: MonoRates,
) -> ConversionResult:
    debit = _estimate_via_mono_rates(amount, card_currency, purchase_currency, rates)

    return ConversionResult(
        debit_amount=debit,
        card_currency=card_currency,
        purchase_amount=amount,
        purchase_currency=purchase_currency,
        explanation=(
            f"Для {purchase_currency} банк зазвичай використовує курс Visa/Mastercard. "
            "Публічний API Monobank не повертає курс платіжної системи напряму."
        ),
        assumption=_payment_system_assumption(),
        is_estimate=debit is not None,
    )


def _payment_system_result(
    amount: float,
    card_currency: str,
    purchase_currency: str,
) -> ConversionResult:
    return ConversionResult(
        debit_amount=None,
        card_currency=card_currency,
        purchase_amount=amount,
        purchase_currency=purchase_currency,
        explanation=(
            "Для цієї валютної пари потрібен курс платіжної системи Visa або Mastercard. "
            "Публічний API Monobank не повертає ці дані."
        ),
        assumption=_payment_system_assumption(),
    )


def _estimate_via_mono_rates(
    amount: float,
    card_currency: str,
    purchase_currency: str,
    rates: MonoRates,
) -> float | None:
    if card_currency == "UAH":
        rate = rates.rate_to_uah(purchase_currency, "sell")
        return amount * rate if rate else None

    purchase_uah = rates.rate_to_uah(purchase_currency, "sell")
    card_uah = rates.rate_to_uah(card_currency, "buy")
    if purchase_uah is not None and card_uah:
        return amount * purchase_uah / card_uah

    try:
        return amount * rates.cross_rate(purchase_currency, card_currency, "sell")
    except ValueError:
        return None


def _safe_cross(
    amount: float,
    currency_from: str,
    currency_to: str,
    rates: MonoRates,
) -> float | None:
    try:
        return amount * rates.cross_rate(currency_from, currency_to, "sell")
    except ValueError:
        return None


def _payment_system_assumption() -> str:
    return (
        "Фактична сума може відрізнятися: Visa/Mastercard мають власні курси, "
        "які залежать від платіжної системи, дати авторизації/обробки та можливих комісій банку. "
        f"Калькулятори: <a href=\"{VISA_CALCULATOR_URL}\">Visa</a>, "
        f"<a href=\"{MASTERCARD_CALCULATOR_URL}\">Mastercard</a>."
    )
