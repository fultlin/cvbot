import asyncio
import sqlite3
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher()

conn = sqlite3.connect("analytics.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS progress (
    user_id INTEGER,
    step TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, step)
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS reminders (
    user_id INTEGER,
    reminder_type TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response TEXT DEFAULT NULL
)
""")
conn.commit()

class CourseCallback(CallbackData, prefix="course"):
    action: str

WELCOME_MESSAGE = "\U0001F44B Добро пожаловать! Нажмите 'Начать', чтобы получить доступ к курсу."

LESSONS = {
    "lesson_1": {
        "text": "\U0001F3A5 Вот первый урок. Приятного просмотра!",
        "url": "https://example.com/lesson1",
        "reminders": [
            "Все уже смотрят второй урок, присоединяйся! Готов поспорить, большинство ошибок ты совершаешь именно по тем причинам, о которых я говорю во втором уроке. Удели всего 5 минут и твоя торговля изменится. Кнопка \"СМОТРЕТЬ\"",
            "Спойлер, о котором узнаешь только ты и только потому, что решил сдаться слишком рано. У тебя есть возможность получить консультацию от топового трейдера из моей команды. Ты сможешь задать любые вопросы по рынку. Но только если полностью пройдешь мини-курс. Действуй, второго шанса не будет. Кнопка \"СМОТРЕТЬ\""
        ]
    },
    "lesson_2": {
        "text": "\U0001F3A5 Вот второй урок. Приятного просмотра!",
        "url": "https://example.com/lesson2",
        "reminders": [
            "Имя, представь, что ты научился предсказывать будущее… И теперь каждая твоя сделка отрабатывает в плюс. Ты больше не сидишь часами у графиков. Ты находишь идеальную точку входа и выхода. Цена идёт всегда в ту сторону, в которую захочешь. Но, увы, предсказаниями мы здесь не занимаемся. Для заработка на рынке не нужно гадать, нужно работать с имеющимися фактами на графике. И тебе для этого нужны всего 3 шага. Какие? Смотри второй урок, там все ответы ⤵️"
        ]
    },
    "lesson_3": {
        "text": "\U0001F3A5 Вот третий урок. Приятного просмотра!",
        "url": "https://example.com/lesson3",
        "reminders": [
            "Привет, ты тут? Это Саша. Решил лично написать, чтобы напомнить про третий урок. Знаю, у тебя были вопросы про точку входа и открытые позиции. Посмотри видео, найдешь все ответы. Если что, пиши с вопросами, я на связи. Кнопка \"СМОТРЕТЬ\""
        ]
    }
}

@dp.message(Command(commands=["start"]))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    cursor.execute("""
    INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
    VALUES (?, ?, ?, ?)
    """, (user_id, username, first_name, last_name))
    conn.commit()

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать", callback_data=CourseCallback(action="lesson_1").pack())]
    ])
    await message.answer(WELCOME_MESSAGE, reply_markup=markup)

@dp.callback_query(CourseCallback.filter())
async def callback_query_handler(call: CallbackQuery, callback_data: CourseCallback):
    user_id = call.from_user.id
    action = callback_data.action

    cursor.execute(""" 
    INSERT OR IGNORE INTO progress (user_id, step)
    VALUES (?, ?)
    """, (user_id, action))
    conn.commit()

    if action in LESSONS:
        lesson = LESSONS[action]
        lesson_keys = list(LESSONS.keys())
        current_index = lesson_keys.index(action)
        next_index = current_index + 1
        next_action = lesson_keys[next_index] if next_index < len(lesson_keys) else None

        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Смотреть", url=lesson["url"])]
        ])

        if next_action:
            markup.inline_keyboard.append([InlineKeyboardButton(
                text="Перейти к следующему уроку",
                callback_data=CourseCallback(action=next_action).pack()
            )])

        await call.message.answer(lesson["text"], reply_markup=markup)
        for delay, reminder in enumerate(lesson["reminders"], start=1):
            asyncio.create_task(send_reminder(user_id, action, reminder, delay * 30))

async def send_reminder(user_id: int, step: str, reminder_text: str, delay: int):
    await asyncio.sleep(delay * 60)  # Задержка в минутах
    cursor.execute("""
    SELECT 1 FROM progress WHERE user_id = ? AND step = ?
    """, (user_id, step))
    result = cursor.fetchone()
    if not result:
        cursor.execute("""
        INSERT INTO reminders (user_id, reminder_type)
        VALUES (?, ?)
        """, (user_id, f"reminder_{step}"))
        conn.commit()
        await bot.send_message(user_id, reminder_text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")
