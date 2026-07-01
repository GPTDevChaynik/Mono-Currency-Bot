from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.keyboards.menu import main_menu

router = Router()


@router.callback_query(F.data == "home")
async def home(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()

    await callback.message.edit_text(
        "💰 <b>Mono Currency Bot</b>\n\n"
        "Оберіть дію:",
        reply_markup=main_menu(),
    )

    await callback.answer()
