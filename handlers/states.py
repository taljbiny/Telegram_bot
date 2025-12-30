from aiogram.dispatcher.filters.state import State, StatesGroup

class DepositStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_method = State()
    waiting_for_receipt = State()

class WithdrawalStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_method = State()
    waiting_for_wallet = State()

class SupportStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_admin_reply = State()
