import asyncio
import time
from dataclasses import dataclass

import aiohttp


URL = "https://api.monobank.ua/bank/currency"
CACHE_TTL_SECONDS = 300
CURRENCY_CODES = {
    36: "AUD",
    124: "CAD",
    156: "CNY",
    203: "CZK",
    208: "DKK",
    348: "HUF",
    392: "JPY",
    578: "NOK",
    752: "SEK",
    756: "CHF",
    826: "GBP",
    840: "USD",
    949: "TRY",
    978: "EUR",
    980: "UAH",
    981: "GEL",
    985: "PLN",
}
_cache: "MonoRates | None" = None
_cache_expires_at = 0.0
_cache_lock = asyncio.Lock()


class MonobankRatesError(Exception):
    pass


@dataclass(frozen=True)
class Rate:
    buy: float | None
    sell: float | None
    cross: float | None = None


class MonoRates:
    def __init__(self, pairs: dict[tuple[str, str], Rate]) -> None:
        self._pairs = pairs

    def rate_to_uah(self, currency: str, side: str) -> float | None:
        if currency == "UAH":
            return 1.0

        pair = self._pairs.get((currency, "UAH"))
        if pair is None:
            return None

        value = pair.sell if side == "sell" else pair.buy
        return value or pair.cross

    def cross_rate(self, currency_from: str, currency_to: str, side: str) -> float:
        direct = self._pairs.get((currency_from, currency_to))
        if direct is not None:
            direct_value = direct.sell if side == "sell" else direct.buy
            if direct_value or direct.cross:
                return direct_value or direct.cross

        reverse = self._pairs.get((currency_to, currency_from))
        if reverse is not None:
            reverse_value = reverse.buy if side == "sell" else reverse.sell
            if reverse_value or reverse.cross:
                return 1 / (reverse_value or reverse.cross)

        source = self.rate_to_uah(currency_from, "sell")
        target = self.rate_to_uah(currency_to, "sell")
        if source is None or target is None:
            raise ValueError(f"No rate for {currency_from}->{currency_to}")

        return source / target

    def cross_assumption(self, currency_from: str, currency_to: str) -> str | None:
        if (currency_from, currency_to) in self._pairs:
            return None

        return (
            f"Прямий курс {currency_from}/{currency_to} не знайдено в API, "
            "тому використано наближений розрахунок через UAH."
        )

    def display_rates(self) -> dict[str, Rate]:
        return {
            currency: self._pairs[(currency, "UAH")]
            for currency in ("USD", "EUR", "PLN")
            if (currency, "UAH") in self._pairs
        }


async def get_rates() -> MonoRates:
    global _cache, _cache_expires_at

    now = time.monotonic()
    if _cache is not None and now < _cache_expires_at:
        return _cache

    async with _cache_lock:
        now = time.monotonic()
        if _cache is not None and now < _cache_expires_at:
            return _cache

        try:
            rates = await _fetch_rates()
        except aiohttp.ClientResponseError as error:
            if error.status == 429 and _cache is not None:
                return _cache

            raise MonobankRatesError(
                "Monobank API is temporarily unavailable. Please try again later."
            ) from error
        except aiohttp.ClientError as error:
            if _cache is not None:
                return _cache

            raise MonobankRatesError(
                "Could not load Monobank rates. Please try again later."
            ) from error

        _cache = rates
        _cache_expires_at = time.monotonic() + CACHE_TTL_SECONDS
        return rates


async def _fetch_rates() -> MonoRates:
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as response:
            response.raise_for_status()
            data = await response.json()

    pairs: dict[tuple[str, str], Rate] = {}

    for item in data:
        currency_a = CURRENCY_CODES.get(item.get("currencyCodeA"))
        currency_b = CURRENCY_CODES.get(item.get("currencyCodeB"))
        if currency_a is None or currency_b is None:
            continue

        pairs[(currency_a, currency_b)] = Rate(
            buy=item.get("rateBuy"),
            sell=item.get("rateSell"),
            cross=item.get("rateCross"),
        )

    return MonoRates(pairs)
