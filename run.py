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

ADMINS_ID = [987609477, 8175097513]

async def get_user_info():
    cursor.execute("""
        SELECT u.user_id, u.username, u.first_name, u.last_name, u.joined_at, u.current_step
        FROM users u
    """)
    users = cursor.fetchall()

    if not users:
        return "Пользователей нет в базе."

    user_info = "Содержимое таблицы users:\n"
    for user in users:
        user_info += (
            f"ID Пользователя: <a href='tg://user?id={user[0]}'>{user[0]}</a>,\nЛогин: {user[1]},\nИмя: {user[2]},\nФамилия: {user[3]},\nПрисоединился: {user[4]},\nТекущий шаг: {user[5]}\n------------------\n"
        )
    return user_info

async def user_info_clbck(id: int):
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (id,))


async def get_project_info():
    cursor.execute("""
        SELECT user_id, step, viewed, confirmed, timestamp
        FROM progress
    """)
    progress = cursor.fetchall()

    if not progress:
        return "Нет данных в таблице progress."

    progress_info = "Содержимое таблицы progress:\n"
    for entry in progress:
        progress_info += (
            f"ID Пользователя: <a href='tg://user?id={entry[0]}'>{entry[0]}</a>,\nШаг: {entry[1]},\nПоказан: {'Да' if entry[2]==1 else 'нет'},\nПройден: {'Да' if entry[2]==1 else 'нет'},\n'{entry[4]}'\n---------------\n"
        )
    return progress_info

@dp.message(Command(commands=["admin"]))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMINS_ID:
        await message.answer("У вас нет прав доступа!")
        return

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пользователи", callback_data="users_info")],
        [InlineKeyboardButton(text="Таблица проекта", callback_data="project_info")]
    ])
    
    await message.answer("Админ-панель:", reply_markup=markup)

# Обработка нажатия кнопки для вывода информации о пользователях
@dp.callback_query(lambda c: c.data == "users_info")
async def users_info(call: CallbackQuery):
    if call.from_user.id not in ADMINS_ID:
        await call.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    user_info = await get_user_info()
    await call.message.answer(user_info, parse_mode='HTML')

@dp.callback_query(lambda c: c.data == "project_info")
async def project_info(call: CallbackQuery):
    if call.from_user.id not in ADMINS_ID:
        await call.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    project_info_text = await get_project_info()
    await call.message.answer(project_info_text, parse_mode='HTML')

def update_users_table():
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if "current_step" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN current_step TEXT")
    conn.commit()

update_users_table()

@dp.message(Command(commands=["stat"]))
async def cmd_stat(message: Message):
    cursor.execute("SELECT DISTINCT step FROM progress")
    steps = [row[0] for row in cursor.fetchall()]

    if not steps:
        await message.answer("Нет данных о шагах.")
        return

    stat_message = "Статистика по шагам:\n\n"
    for step in steps:
        cursor.execute("SELECT COUNT(*) FROM progress WHERE step = ? AND viewed = TRUE", (step,))
        viewed_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM progress WHERE step = ? AND confirmed = TRUE", (step,))
        confirmed_count = cursor.fetchone()[0]

        stat_message += (
            f"Шаг {step}:\n"
            f"  Показан: {viewed_count}\n"
            f"  Пройден: {confirmed_count}\n\n"
        )

    await message.answer(stat_message)

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
    viewed BOOLEAN DEFAULT true,
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
REMIDNER = "Ты решил сдаться, ещё не начав? Не надо так. Смотри курс, пока он ещё доступен. "
REMIDNER2 = "Скоро закрою доступ, а ты так и не посмотрел курс\n"
"Не сдавайся на ровном месте. Переходи по кнопке ниже, пока урок не пропал ⤵️"
LESSONS = {
    "lesson_1": {
        "text": "{name}, первый урок уже доступен, скорее открывай его и смотри до конца. В уроке я разобрал: \n"
"   - Какой 1 инструмент нужно знать, чтобы твоя торговая стратегия начала работать. \n"
"   - Почему 95% трейдеров ошибаются в торговле. \n"
"   - Как быть прибыльным на дистанции и жить за счёт рынка. \n"
"Чем раньше посмотришь урок, тем быстрее перестанешь ошибаться в выборе направления цены, жми кнопку ниже ⤵️",
        "url": "https://example.com/lesson1",
        "photo": "https://ibb.org.ru/1/qNlolp",
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
        "photo": "",
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
        "photo": "https://ibb.org.ru/1/qNXqf0",
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
        "photo": "https://ibb.org.ru/1/qNXNzK"
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
    
    cursor.execute("""
    INSERT OR IGNORE INTO progress (user_id, step, viewed)
    VALUES (?, ?, ?)
    """, (user_id, 'start', True))
    conn.commit()
    
    cursor.execute("""
    UPDATE users
    SET current_step = ?
    WHERE user_id = ?
    """, ('start', user_id))
    conn.commit()

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Забрать ⬇️", callback_data=CourseCallback(action="lesson_1", type="view").pack())]
    ])
    await bot.send_photo(chat_id=message.chat.id, photo='https://ibb.org.ru/1/qNlgvm', caption=WELCOME_MESSAGE, reply_markup=markup)

    asyncio.create_task(send_reminder(user_id, 'start', REMIDNER, delay=5))
    asyncio.create_task(send_reminder(user_id, 'start', REMIDNER2, delay=30))
    
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
        UPDATE progress
        SET viewed = TRUE, confirmed = TRUE
        WHERE user_id = ? AND step = ?
        """, (user_id, 'start'))
        conn.commit()

        cursor.execute("""
        INSERT OR IGNORE INTO progress (user_id, step, viewed)
        VALUES (?, ?, ?)
        """, (user_id, action, True))
        conn.commit()
        
        cursor.execute("""
        UPDATE users
        SET current_step = ?
        WHERE user_id = ?
        """, (action, user_id))
        conn.commit()

        if action in LESSONS:
            lesson = LESSONS[action]
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Смотреть", url=lesson["url"])],
                [InlineKeyboardButton(text="Я посмотрел", callback_data=CourseCallback(action=action, type="confirm").pack())]
            ])
            await bot.send_photo(
                chat_id=call.message.chat.id,
                photo=lesson["photo"],
                caption=lesson["text"].format(name=name),
                reply_markup=markup
            )

            asyncio.create_task(send_reminder(user_id, action, lesson["reminders"][0], delay=5))
            if (lesson["reminders"] and len(lesson["reminders"]) > 1):
                asyncio.create_task(send_reminder(user_id, action, lesson["reminders"][1], delay=30))

    elif type_ == "confirm":
        cursor.execute("""
        UPDATE progress
        SET viewed = TRUE, confirmed = TRUE
        WHERE user_id = ? AND step = ?
        """, (user_id, action))
        conn.commit()

        cursor.execute("""
        INSERT OR IGNORE INTO progress (user_id, step, viewed)
        VALUES (?, ?, ?)
        """, (user_id, action, True))
        conn.commit()
        
        next_lesson = LESSONS[action].get("next")
        if next_lesson:
            cursor.execute("""
            UPDATE users
            SET current_step = ?
            WHERE user_id = ?
            """, (next_lesson, user_id))
            conn.commit()

        await call.answer("Спасибо, что подтвердили просмотр!", show_alert=True)

        if action == "lesson_3":
            final_lesson = LESSONS["final"]
            await bot.send_photo(
                chat_id=call.message.chat.id,
                photo=final_lesson["photo"],
                caption=final_lesson["text"].format(name=name)
            )
        else:
            next_lesson = LESSONS[action].get("next")
            if next_lesson and next_lesson in LESSONS:
                lesson = LESSONS[next_lesson]
                asyncio.create_task(send_reminder(user_id, next_lesson, lesson["reminders"][0], delay=5))
                
                if len(lesson["reminders"]) > 1:
                    asyncio.create_task(send_reminder(user_id, next_lesson, LESSONS[next_lesson]["reminders"][1], delay=30))

                cursor.execute("""
                INSERT OR IGNORE INTO progress (user_id, step, viewed)
                VALUES (?, ?, ?)
                """, (user_id, next_lesson, True))  
                conn.commit()

                lesson = LESSONS[next_lesson]
                markup = InlineKeyboardMarkup(inline_keyboard=[  
                    [InlineKeyboardButton(text="Смотреть", url=lesson["url"])],
                    [InlineKeyboardButton(text="Я посмотрел", callback_data=CourseCallback(action=next_lesson, type="confirm").pack())]
                ])
                if lesson["photo"]:
                    await bot.send_photo(
                        chat_id=call.message.chat.id,
                        photo=lesson["photo"],  
                        caption=lesson['text'].format(name=name),  
                        reply_markup=markup  
                    )
                else:
                    await bot.send_message(
                        chat_id=call.message.chat.id,
                        text=lesson['text'].format(name=name),
                        reply_markup=markup
                    )
                

async def send_reminder(user_id: int, step: str, reminder_text: str, delay: int):
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
    
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")

