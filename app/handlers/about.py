from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.keyboards.menu import home_menu

router = Router()


@router.callback_query(F.data == "about")
async def about(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "ℹ️ <b>Як працює конвертація</b>\n\n"
        "• Гривнева картка: USD/EUR конвертуються в UAH за курсом продажу Monobank. "
        "Інші валюти можуть проходити через курс Visa/Mastercard, потім через USD в UAH.\n\n"
        "• Доларова картка: EUR конвертується в USD за курсом продажу Monobank, "
        "UAH — в USD за курсом купівлі. Інші валюти залежать від Visa/Mastercard.\n\n"
        "• Єврова картка: USD конвертується в EUR за курсом продажу Monobank, "
        "UAH — в EUR за курсом купівлі. Інші валюти залежать від Visa/Mastercard.\n\n"
        "• GEL, GBP, CHF, CZK, TRY та інші валюти: бот може показати орієнтовний розрахунок "
        "через доступні курси Monobank API, але фактичне списання залежить від Visa/Mastercard.\n\n"
        "Публічний API Monobank не повертає курси платіжних систем, тому для таких операцій "
        "бот показує попередження та посилання на офіційні калькулятори Visa/Mastercard.",
        reply_markup=home_menu(),
    )
    await callback.answer()
