from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.keyboards.menu import rates_menu
from app.services.monobank import MonobankRatesError, get_rates
from app.services.telegram import safe_edit_text

router = Router()


@router.callback_query(F.data == "rates")
async def show_rates(callback: CallbackQuery) -> None:
    try:
        rates = await get_rates()
    except MonobankRatesError:
        await safe_edit_text(
            callback.message,
            "⚠️ <b>Курси тимчасово недоступні</b>\n\n"
            "Monobank API зараз не відповідає або обмежив кількість запитів. "
            "Спробуйте оновити трохи пізніше.",
            reply_markup=rates_menu(),
        )
        await callback.answer()
        return

    display_rates = rates.display_rates()

    lines = ["💰 <b>Курси Monobank</b>", ""]
    for currency in ("USD", "EUR", "PLN"):
        rate = display_rates.get(currency)
        if rate is None:
            lines.append(f"{currency}: немає даних")
            continue

        buy = _format_rate(rate.buy or rate.cross)
        sell = _format_rate(rate.sell or rate.cross)
        lines.extend(
            [
                f"<b>{currency}</b>",
                f"Купівля: <b>{buy}</b>",
                f"Продаж: <b>{sell}</b>",
                "",
            ]
        )

    changed = await safe_edit_text(
        callback.message,
        "\n".join(lines).strip(),
        reply_markup=rates_menu(),
    )

    await callback.answer("Курси вже актуальні" if not changed else None)


def _format_rate(value: float | None) -> str:
    return f"{value:.2f}" if value is not None else "немає даних"
