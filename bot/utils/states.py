from aiogram.fsm.state import StatesGroup, State


class SearchByTime(StatesGroup):
    waiting_for_date = State()
    waiting_for_slots = State()
