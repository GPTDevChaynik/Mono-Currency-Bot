from dataclasses import dataclass

from app.services.monobank import MonoRates


CARD_CURRENCIES = ("UAH", "USD", "EUR")
PURCHASE_CURRENCIES = ("UAH", "USD", "EUR", "PLN")


@dataclass(frozen=True)
class ConversionResult:
    debit_amount: float | None
    card_currency: str
    purchase_amount: float
    purchase_currency: str
    explanation: str
    assumption: str | None = None


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

    if card_currency not in CARD_CURRENCIES or purchase_currency not in PURCHASE_CURRENCIES:
        return _payment_system_result(amount, card_currency, purchase_currency)

    if card_currency == "UAH":
        return _to_uah_card(amount, purchase_currency, rates)

    if card_currency == "USD":
        return _to_usd_card(amount, purchase_currency, rates)

    return _to_eur_card(amount, purchase_currency, rates)


def _to_uah_card(amount: float, purchase_currency: str, rates: MonoRates) -> ConversionResult:
    rate = rates.rate_to_uah(purchase_currency, "sell")
    if rate is None:
        return _payment_system_result(amount, "UAH", purchase_currency)

    return ConversionResult(
        debit_amount=amount * rate,
        card_currency="UAH",
        purchase_amount=amount,
        purchase_currency=purchase_currency,
        explanation=f"{purchase_currency} конвертується в UAH за курсом продажу Monobank.",
        assumption=_pln_assumption(purchase_currency),
    )


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
        return ConversionResult(
            debit_amount=amount * rates.cross_rate("EUR", "USD", "sell"),
            card_currency="USD",
            purchase_amount=amount,
            purchase_currency="EUR",
            explanation="EUR конвертується в USD за курсом продажу Monobank.",
            assumption=rates.cross_assumption("EUR", "USD"),
        )

    if purchase_currency == "PLN":
        return _via_uah_bridge(amount, "USD", "PLN", rates)

    return _payment_system_result(amount, "USD", purchase_currency)


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
        return ConversionResult(
            debit_amount=amount * rates.cross_rate("USD", "EUR", "sell"),
            card_currency="EUR",
            purchase_amount=amount,
            purchase_currency="USD",
            explanation="USD конвертується в EUR за курсом продажу Monobank.",
            assumption=rates.cross_assumption("USD", "EUR"),
        )

    if purchase_currency == "PLN":
        return _via_uah_bridge(amount, "EUR", "PLN", rates)

    return _payment_system_result(amount, "EUR", purchase_currency)


def _via_uah_bridge(
    amount: float,
    card_currency: str,
    purchase_currency: str,
    rates: MonoRates,
) -> ConversionResult:
    purchase_sell = rates.rate_to_uah(purchase_currency, "sell")
    card_buy = rates.rate_to_uah(card_currency, "buy")
    debit = amount * purchase_sell / card_buy if purchase_sell and card_buy else None

    return ConversionResult(
        debit_amount=debit,
        card_currency=card_currency,
        purchase_amount=amount,
        purchase_currency=purchase_currency,
        explanation=(
            f"{purchase_currency} розраховано через UAH за доступним курсом API, "
            f"потім UAH конвертовано в {card_currency} за курсом купівлі."
        ),
        assumption=(
            "Це наближений розрахунок: для таких операцій банк може використовувати "
            "курс Visa/Mastercard, якого немає в публічному API Monobank."
        ),
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
    )


def _pln_assumption(purchase_currency: str) -> str | None:
    if purchase_currency != "PLN":
        return None

    return (
        "Для PLN використано доступний курс Monobank API. Якщо операція проходить "
        "як конвертація платіжної системи, фактична сума може відрізнятися."
    )
