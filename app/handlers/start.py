from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.keyboards.menu import main_menu

router = Router()


@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        "💰 <b>Mono Currency Bot</b>\n\n"
        "Оберіть дію:",
        reply_markup=main_menu(),
    )
