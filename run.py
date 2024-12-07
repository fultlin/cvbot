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

def update_progress_table():
    cursor.execute("PRAGMA table_info(progress)")
    columns = [column[1] for column in cursor.fetchall()]
    if "viewed" not in columns:
        cursor.execute("ALTER TABLE progress ADD COLUMN viewed BOOLEAN DEFAULT FALSE")
    if "confirmed" not in columns:
        cursor.execute("ALTER TABLE progress ADD COLUMN confirmed BOOLEAN DEFAULT FALSE")
    conn.commit()

update_progress_table()

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
    viewed BOOLEAN DEFAULT FALSE,
    confirmed BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, step)
)
""")
conn.commit()

class CourseCallback(CallbackData, prefix="course"):
    action: str
    type: str

WELCOME_MESSAGE = "Тебе очень повезло! Всего за 3 урока я пошагово передам тебе свою авторскую стратегию торговли, которую ты с лёгкостью освоишь уже сегодня. Мой метод работает в 70% случаев и его протестировали уже более 300 человек. Они отмечают, что раньше не могли найти точку входа в сделку, но после просмотра этих трёх роликов, они научились грамотно открывать позиции. Ты готов забрать мою стратегию? Жми на кнопку ЗАБРАТЬ ⬇️"

LESSONS = {
    "lesson_1": {
        "text": "{name}, первый урок уже доступен, скорее открывай его и смотри до конца. В уроке я разобрал: \n"
"   - Какой 1 инструмент нужно знать, чтобы твоя торговая стратегия начала работать. \n"
"   - Почему 95% трейдеров ошибаются в торговле. \n"
"   - Как быть прибыльным на дистанции и жить за счёт рынка. \n"
"Чем раньше посмотришь урок, тем быстрее перестанешь ошибаться в выборе направления цены, жми кнопку ниже ⤵️",
        "url": "https://example.com/lesson1",
        "reminders": [
            "Все уже смотрят второй урок, присоединяйся! Готов поспорить, большинство ошибок ты совершаешь именно по тем причинам, о которых я говорю во втором уроке. Удели всего 5 минут и твоя торговля изменится.",
            "Спойлер, о котором узнаешь только ты и только потому, что решил сдаться слишком рано У тебя есть возможность получить консультацию от топового трейдера из моей команды. Ты сможешь задать любые вопросы по рынку, но только если полностью пройдешь мини курс. Действуй, второго шанса не будет"
        ],
        "next": "lesson_2"
    },
    "lesson_2": {
        "text": "{name}, представь, что ты научился предсказывать будущее…\n"
"   - И теперь каждая твоя сделка отрабатывает в плюс. \n"
"   - Ты больше не сидишь часами у графиков. \n"
"   - Ты находишь идеальную точку входа и выхода. \n"
"   - Цена идёт всегда в ту сторону, в которую захочешь. \n"
"…но, увы, предсказаниями мы здесь не занимаемся. Для заработка на рынке не нужно гадать, нужно работать с имеющимися фактами на графике. "
"И тебе для этого нужны всего 3 шага. "
"Какие? Смотри второй урок, там все ответы ⤵️ ",
        "url": "https://example.com/lesson2",
        "reminders": [
            "У тебя есть возможность получить консультацию от трейдера, смотри второй урок! Кнопка \"СМОТРЕТЬ\"",
        ],
        "next": "lesson_3"
    },
    
    "lesson_3": {
        "text": "{name}, молодец, ты на верном пути!\n"
"В третьем уроке я объясню тебе последний шаг, который позволяет находить идеальную точку входа в сделке. \n"
"И знаешь, среди 300 человек, которые применили мою стратегию, все отметили важность понимания именно третьего шага. \n"
"Уверен, у тебя всё получится. Я готов провести тебя за руку до результата. \n"
"Посмотри третье видео и не забудь забрать подарок. \n",
        "url": "https://example.com/lesson3",
        "reminders": [
            "Привет, ты тут? Это Саша\n"
            "Решил лично написать, чтобы напомнить про третий урок.\n"
            "Знаю, у тебя были вопросы про точку входа и открытые позиции. Посмотри видео, найдешь все ответы. Если что, пиши с вопросами, я на связи.\n"
        ],
        "next": "final"
    },
    
    "final" : {
        "text": "{name}, поздравляю с прохождением мини-курса! Ты молодец 🤝🏽\n"
"Теперь у тебя есть понимание основ моей стратегии. \n"
"И я тебе дарю уникальный 🎁 подарок: \n"
"Карту с пошаговым планом входа в сделку, которую ты видел в мини курсе. Ранее ее стоимость была 100$, сейчас ты можешь забрать ее бесплатно. \n"
"Также, только в следующие 48 часов у тебя будет возможность записаться на консультацию с топовым трейдером из моей команды. \n"
"На консультации ты сможешь задать любые вопросы и разобрать свою торговую систему (если она есть). \n"
"Раньше эту консультацию мы проводили за 500$, но для учеников с мини курса мы решили сделать исключение. \n"
"Чтобы забрать карту и записаться на консультацию, напиши своему куратору @ слово «хочу» и он вышлет тебе всю информацию. \n"
"Аккаунт твоего куратора -> @\n"
"Мы будем рады поделиться с тобой пользой.",
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
        [InlineKeyboardButton(text="Забрать ⬇️", callback_data=CourseCallback(action="lesson_1", type="view").pack())]
    ])
    await message.answer(WELCOME_MESSAGE, reply_markup=markup)
    
@dp.callback_query(CourseCallback.filter())
async def callback_query_handler(call: CallbackQuery, callback_data: CourseCallback):
    user_id = call.from_user.id
    action = callback_data.action
    type_ = callback_data.type

    cursor.execute("SELECT first_name FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    name = result[0] if result else "Имя"

    if type_ == "view":
        cursor.execute("""
        INSERT OR IGNORE INTO progress (user_id, step, viewed)
        VALUES (?, ?, ?)
        """, (user_id, action, True))
        conn.commit()

        if action in LESSONS:
            lesson = LESSONS[action]
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Смотреть", url=lesson["url"])],
                [InlineKeyboardButton(text="Я посмотрел", callback_data=CourseCallback(action=action, type="confirm").pack())]
            ])
            await call.message.answer(lesson["text"].format(name=name), reply_markup=markup)

            
            asyncio.create_task(send_reminder(user_id, action, lesson["reminders"][0], delay=5))
            asyncio.create_task(send_reminder(user_id, action, lesson["reminders"][1], delay=30))

    elif type_ == "confirm":
        cursor.execute("""
        UPDATE progress
        SET confirmed = TRUE
        WHERE user_id = ? AND step = ?
        """, (user_id, action))
        conn.commit()
        await call.answer("Спасибо, что подтвердили просмотр!", show_alert=True)

        if action == "lesson_3":
            final_lesson = LESSONS["final"]
            await call.message.answer(final_lesson['text'].format(name=name))
        else:
            next_lesson = LESSONS[action].get("next")
            if next_lesson and next_lesson in LESSONS:
                lesson = LESSONS[next_lesson]
                markup = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Смотреть", url=lesson["url"])],
                    [InlineKeyboardButton(text="Я посмотрел", callback_data=CourseCallback(action=next_lesson, type="confirm").pack())]
                ])
                await call.message.answer(lesson['text'].format(name=name), reply_markup=markup)


async def send_reminder(user_id: int, step: str, reminder_text: str, delay: int):
    await asyncio.sleep(delay * 60) 
    cursor.execute("""
    SELECT confirmed FROM progress WHERE user_id = ? AND step = ?
    """, (user_id, step))
    result = cursor.fetchone()

    if result and not result[0]:  
        await bot.send_message(user_id, reminder_text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")

