from aiogram.fsm.state import State, StatesGroup


class GenerateStates(StatesGroup):
    collecting = State()
    result = State()
