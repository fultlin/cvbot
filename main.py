import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from handlers import cmd_start, cmd_admin, get_user_by_id, request_user_id, users_info, project_info, callback_query_handler  # Импортируем обработчики
from config import TOKEN
from models import CourseCallback  

bot = Bot(token=TOKEN)
dp = Dispatcher()

dp.message.register(cmd_start, Command("start"))
dp.message.register(cmd_admin, Command("admin"))
dp.callback_query.register(callback_query_handler, CourseCallback.filter())
dp.callback_query.register(users_info, lambda c: c.data == "users_info")
dp.callback_query.register(project_info, lambda c: c.data == "project_info")
dp.callback_query.register(request_user_id, lambda c: c.data == "request_user_id")
dp.message.register(get_user_by_id, lambda message: message.text.isdigit()) 

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")
