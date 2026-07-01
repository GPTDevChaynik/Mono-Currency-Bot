from aiogram import Bot, Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.keyboards.menu import currency_menu, result_menu
from app.services.currency_converter import CARD_CURRENCIES, PURCHASE_CURRENCIES, ConversionResult, convert_purchase
from app.services.monobank import MonobankRatesError, get_rates
from app.services.telegram import safe_bot_edit_text
from app.states import ConverterState

router = Router()


@router.callback_query(F.data == "converter")
async def converter(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ConverterState.waiting_card_currency)
    await state.update_data(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
    )

    await callback.message.edit_text(
        "💳 <b>Конвертер</b>\n\n"
        "Оберіть валюту картки:",
        reply_markup=currency_menu("card", CARD_CURRENCIES),
    )

    await callback.answer()


@router.callback_query(ConverterState.waiting_card_currency, F.data.startswith("card:"))
async def choose_card_currency(callback: CallbackQuery, state: FSMContext) -> None:
    card_currency = callback.data.split(":", maxsplit=1)[1]
    await state.update_data(card_currency=card_currency)
    await state.set_state(ConverterState.waiting_purchase_currency)

    await callback.message.edit_text(
        "💳 <b>Конвертер</b>\n\n"
        f"Валюта картки: <b>{card_currency}</b>\n"
        "Оберіть валюту покупки:",
        reply_markup=currency_menu("purchase", PURCHASE_CURRENCIES),
    )

    await callback.answer()


@router.callback_query(ConverterState.waiting_purchase_currency, F.data.startswith("purchase:"))
async def choose_purchase_currency(callback: CallbackQuery, state: FSMContext) -> None:
    purchase_currency = callback.data.split(":", maxsplit=1)[1]
    data = await state.get_data()
    card_currency = data["card_currency"]
    await state.update_data(purchase_currency=purchase_currency)
    await state.set_state(ConverterState.waiting_amount)

    await callback.message.edit_text(
        "💳 <b>Конвертер</b>\n\n"
        f"Валюта картки: <b>{card_currency}</b>\n"
        f"Валюта покупки: <b>{purchase_currency}</b>\n\n"
        "Введіть суму покупки одним повідомленням.",
    )

    await callback.answer()


@router.message(ConverterState.waiting_amount)
async def convert(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    chat_id = data["chat_id"]
    message_id = data["message_id"]

    try:
        amount = float((message.text or "").replace(",", "."))
    except ValueError:
        await safe_bot_edit_text(
            bot,
            chat_id,
            message_id,
            (
                "❌ <b>Некоректна сума</b>\n\n"
                "Введіть число, наприклад <b>1250.50</b>."
            ),
        )
        return

    if amount <= 0:
        await safe_bot_edit_text(
            bot,
            chat_id,
            message_id,
            (
                "❌ <b>Некоректна сума</b>\n\n"
                "Сума має бути більшою за нуль."
            ),
        )
        return

    try:
        rates = await get_rates()
    except MonobankRatesError:
        await safe_bot_edit_text(
            bot,
            chat_id,
            message_id,
            "⚠️ <b>Курси тимчасово недоступні</b>\n\n"
            "Monobank API зараз не відповідає або обмежив кількість запитів. "
            "Спробуйте розрахунок трохи пізніше.",
            reply_markup=result_menu(),
        )
        await state.clear()
        return

    result = convert_purchase(
        amount=amount,
        card_currency=data["card_currency"],
        purchase_currency=data["purchase_currency"],
        rates=rates,
    )

    await safe_bot_edit_text(
        bot,
        chat_id,
        message_id,
        _format_result(result),
        reply_markup=result_menu(),
    )

    await state.clear()


def _format_result(result: ConversionResult) -> str:
    lines = [
        "💳 <b>Результат конвертації</b>",
        "",
        f"Покупка: <b>{result.purchase_amount:.2f} {result.purchase_currency}</b>",
    ]

    if result.debit_amount is None:
        lines.append("Списання: <b>потрібен курс Visa/Mastercard</b>")
    elif result.is_estimate:
        lines.append(f"Орієнтовне списання: <b>{result.debit_amount:.2f} {result.card_currency}</b>")
    else:
        lines.append(f"Списання: <b>{result.debit_amount:.2f} {result.card_currency}</b>")

    lines.extend(["", result.explanation])

    if result.assumption:
        lines.extend(["", f"⚠️ {result.assumption}"])

    return "\n".join(lines)
