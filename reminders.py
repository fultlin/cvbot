import asyncio
import logging
from db import cursor, conn
from aiogram import Bot

async def send_reminder(bot: Bot, user_id: int, step: str, reminder_text: str, delay: int):
    logging.info(f"Создано напоминание для пользователя {user_id}")
    await asyncio.sleep(delay * 60)
    cursor.execute("""
    SELECT confirmed FROM progress WHERE user_id = ? AND step = ?
    """, (user_id, step))
    result = cursor.fetchone()

    if not result:
        print(f"Урок {step} для пользователя {user_id} не найден.")
        return

    if result[0]:
        print(f"Урок {step} для пользователя {user_id} уже подтвержден.")
        return

    await bot.send_message(user_id, reminder_text)
