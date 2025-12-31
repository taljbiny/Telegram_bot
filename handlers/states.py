from aiogram.dispatcher.filters.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_password = State()
    waiting_for_phone = State()

class DepositStates(StatesGroup):
    waiting_for_method = State()
    waiting_for_amount = State()
    waiting_for_transaction_id = State()

class WithdrawalStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_method = State()
    waiting_for_wallet = State()

class SupportStates(StatesGroup):
    waiting_for_message = State()
