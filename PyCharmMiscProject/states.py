from aiogram.fsm.state import State, StatesGroup
class ProfileStates(StatesGroup):
    waiting_email = State()
    waiting_phone = State()

class ReminderStates(StatesGroup):
    waiting_text = State()
    waiting_time = State()

class SearchStates(StatesGroup):
    waiting_query = State()