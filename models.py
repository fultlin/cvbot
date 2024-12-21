from aiogram.filters.callback_data import CallbackData

class CourseCallback(CallbackData, prefix="course"):
    action: str
    type: str