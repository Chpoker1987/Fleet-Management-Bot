from aiogram.fsm.state import State, StatesGroup

class VehicleForm(StatesGroup):
    """
    Машина состояний для процесса добавления нового автомобиля.
    Шаг 1: Ожидание номера (plate)
    Шаг 2: Ожидание имени водителя (driver)
    """
    waiting_for_plate = State()
    waiting_for_driver = State()
