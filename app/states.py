from aiogram.fsm.state import State, StatesGroup


class ConverterState(StatesGroup):
    waiting_card_currency = State()
    waiting_purchase_currency = State()
    waiting_amount = State()
