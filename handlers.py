import asyncio
import logging
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot
from config import ADMINS_ID
from db import get_project_info, get_user_info, insert_user, insert_progress, update_user_step, cursor, conn
from models import CourseCallback
from text import LESSONS, REMIDNER, REMIDNER2, WELCOME_MESSAGE
from reminders import send_reminder

logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

async def cmd_admin(message: Message):
    if message.from_user.id not in ADMINS_ID:
        await message.answer("У вас нет прав доступа!")
        logging.warning(f"Попытка доступа к админ-панели от пользователя: {message.from_user.id}")
        return

    markup = InlineKeyboardMarkup(inline_keyboard=[ 
        [InlineKeyboardButton(text="Поиск по пользователю", callback_data="search_by_user")]
    ])

    await message.answer("Админ-панель:", reply_markup=markup)
    logging.warning(f"Пользователь {message.from_user.id} открыл админ-панель")


async def search_by_user(call: CallbackQuery):
    if call.from_user.id not in ADMINS_ID:
        await call.answer("У вас нет прав доступа!", show_alert=True)
        logging.warning(f"Попытка доступа к поиску пользователя {call.from_user.id}")
        return

    markup = InlineKeyboardMarkup(inline_keyboard=[ 
        [InlineKeyboardButton(text="Поиск по ID", callback_data="search_by_id")],
        [InlineKeyboardButton(text="Поиск по никнейму", callback_data="search_by_username")]
    ])
    
    await call.message.answer("Выберите способ поиска пользователя:", reply_markup=markup)
    await call.answer()
    logging.warning(f"{call.from_user.id} выбрал способ поиска пользователя")


async def search_by_id(call: CallbackQuery):
    if call.from_user.id not in ADMINS_ID:
        await call.answer("У вас нет прав доступа!", show_alert=True)
        return

    await call.message.answer("Пожалуйста, введите ID пользователя для получения информации:")
    await call.answer()
    logging.warning(f"Пользователь {call.from_user.id} вводит ID пользователя")

async def search_by_username(call: CallbackQuery):
    if call.from_user.id not in ADMINS_ID:
        await call.answer("У вас нет прав доступа!", show_alert=True)
        return

    await call.message.answer("Пожалуйста, введите никнейм пользователя для получения информации (@exmp):")
    await call.answer()
    logging.warning(f"Пользователь {call.from_user.id} вводит никнейм пользователя")


async def get_user_by_id(message: Message):
    user_id = int(message.text)

    cursor.execute("""
        SELECT username, first_name, last_name, joined_at, current_step
        FROM users
        WHERE user_id = ?
    """, (user_id,))
    user_info = cursor.fetchone()

    if user_info:
        user_details = (
            f"ID: {user_id}\n"
            f"Логин: {user_info[0]}\n"
            f"Имя: {user_info[1]}\n"
            f"Фамилия: {user_info[2]}\n"
            f"Дата регистрации: {user_info[3]}\n"
            f"Текущий шаг: {user_info[4]}\n"
        )
    else:
        user_details = f"Пользователь с ID {user_id} не найден."

    cursor.execute("""
        SELECT step, viewed, confirmed, timestamp
        FROM progress
        WHERE user_id = ?
    """, (user_id,))
    progress = cursor.fetchall()

    if progress:
        progress_details = "Прогресс пользователя:\n"
        for entry in progress:
            progress_details += (
                f"Шаг: {entry[0]}, Пройден: {'Да' if entry[2] else 'Нет'}, "
                f"Просмотрен: {'Да' if entry[1] else 'Нет'}, Время: {entry[3]}\n"
            )
    else:
        progress_details = "Прогресс не найден."

    await message.answer(user_details)
    await message.answer(progress_details)
    logging.warning(f"Выведена информация для пользователя с ID: {user_id}")


async def get_user_by_username(message: Message):
    username = message.text.strip() 
    username = username.replace('@', '')

    cursor.execute("""
        SELECT user_id, first_name, last_name, joined_at, current_step
        FROM users
        WHERE username = ?
    """, (username,))
    user_info = cursor.fetchone()

    if user_info:
        user_details = (
            f"ID: {user_info[0]}\n"
            f"Логин: {username}\n"
            f"Имя: {user_info[1]}\n"
            f"Фамилия: {user_info[2]}\n"
            f"Дата регистрации: {user_info[3]}\n"
            f"Текущий шаг: {user_info[4]}\n"
        )

        cursor.execute("""
            SELECT step, viewed, confirmed, timestamp
            FROM progress
            WHERE user_id = ?
        """, (user_info[0],))
        progress = cursor.fetchall()

        if progress:
            progress_details = "Прогресс пользователя:\n"
            for entry in progress:
                progress_details += (
                    f"Шаг: {entry[0]}, Пройден: {'Да' if entry[2] else 'Нет'}, "
                    f"Просмотрен: {'Да' if entry[1] else 'Нет'}, Время: {entry[3]}\n"
                )
        else:
            progress_details = "Прогресс не найден."
        
        await message.answer(user_details)
        await message.answer(progress_details)
        logging.warning(f"Выведена информация для пользователя с ником {username}")

    else:
        await message.answer(f"Пользователь с никнеймом {username} не найден.")


async def request_user_id(call: CallbackQuery):
    if call.from_user.id not in ADMINS_ID:
        await call.answer("У вас нет прав доступа!", show_alert=True)
        logging.warning(f"Попытка пользователя {call.from_user.id} получить доступ к поиску по айди")
        return

    await call.message.answer("Пожалуйста, введите ID пользователя для получения информации:")
    await call.answer()
    logging.warning(f"Пользователь {call.from_user.id} ввёл ID пользователя")


async def get_user_by_id(message: Message):
    user_id = int(message.text)

    cursor.execute("""
        SELECT username, first_name, last_name, joined_at, current_step
        FROM users
        WHERE user_id = ?
    """, (user_id,))
    user_info = cursor.fetchone()

    if user_info:
        user_details = (
            f"ID: {user_id}\n"
            f"Логин: {user_info[0]}\n"
            f"Имя: {user_info[1]}\n"
            f"Фамилия: {user_info[2]}\n"
            f"Дата регистрации: {user_info[3]}\n"
            f"Текущий шаг: {user_info[4]}\n"
        )
    else:
        user_details = f"Пользователь с ID {user_id} не найден."

    cursor.execute("""
        SELECT step, viewed, confirmed, timestamp
        FROM progress
        WHERE user_id = ?
    """, (user_id,))
    progress = cursor.fetchall()

    if progress:
        progress_details = "Прогресс пользователя:\n"
        for entry in progress:
            progress_details += (
                f"Шаг: {entry[0]}, Пройден: {'Да' if entry[2] else 'Нет'}, "
                f"Просмотрен: {'Да' if entry[1] else 'Нет'}, Время: {entry[3]}\n"
            )
    else:
        progress_details = "Прогресс не найден."

    await message.answer(user_details)
    await message.answer(progress_details)
    logging.warning(f"Выведена информация для пользователя: {user_id}")

async def users_info(call: CallbackQuery):
    if call.from_user.id not in ADMINS_ID:
        await call.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    user_info = await get_user_info()
    await call.message.answer(user_info, parse_mode='HTML')

async def project_info(call: CallbackQuery):
    if call.from_user.id not in ADMINS_ID:
        await call.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    project_info_text = await get_project_info()
    await call.message.answer(project_info_text, parse_mode='HTML')

async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    insert_user(user_id, username, first_name, last_name)
    insert_progress(user_id, 'start')

    update_user_step(user_id, 'start')

    markup = InlineKeyboardMarkup(inline_keyboard=[ 
        [InlineKeyboardButton(text="Забрать ⬇️", callback_data=CourseCallback(action="lesson_1", type="view").pack())] 
    ])
        
    await bot.send_photo(chat_id=message.chat.id, photo='https://ibb.org.ru/1/qNlgvm', caption=WELCOME_MESSAGE, reply_markup=markup)
    logging.warning(f"Начало общения с пользователем: {user_id}. Отправлено приветственное сообщение")


    asyncio.create_task(send_reminder(bot, user_id, 'start', REMIDNER, delay=5))
    asyncio.create_task(send_reminder(bot, user_id, 'start', REMIDNER2, delay=30))

async def callback_query_handler(call: CallbackQuery, callback_data: CourseCallback, bot: Bot):
    user_id = call.from_user.id
    action = callback_data.action
    type_ = callback_data.type

    cursor.execute("SELECT first_name FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    name = result[0] if result else "Имя"

    print(f"Callback received for action: {action}, type: {type_}, user_id: {user_id}")

    if type_ == "view":
        cursor.execute(""" 
        UPDATE progress SET viewed = TRUE, confirmed = TRUE WHERE user_id = ? AND step = ?""", (user_id, 'start'))
        conn.commit()

        cursor.execute("""
        INSERT OR IGNORE INTO progress (user_id, step, viewed) VALUES (?, ?, ?)""", (user_id, action, True))
        conn.commit()

        cursor.execute("""UPDATE users SET current_step = ? WHERE user_id = ?""", (action, user_id))
        conn.commit()

        if action in LESSONS:
            lesson = LESSONS[action]
            print(f"Sending lesson {action} to user {user_id}: {lesson}")

            markup = InlineKeyboardMarkup(inline_keyboard=[ 
                [InlineKeyboardButton(text="Смотреть", url=lesson["url"])], 
                [InlineKeyboardButton(text="Я посмотрел", callback_data=CourseCallback(action=action, type="confirm").pack())] 
            ])
            
            try:
                await bot.send_photo(
                    chat_id=call.message.chat.id,
                    photo=lesson["photo"],
                    caption=lesson["text"].format(name=name),
                    reply_markup=markup
                )
                logging.warning(f"Отправлен урок {lesson} для пользователя: {user_id}")

            except Exception as e:
                print(f"Error sending photo: {e}")
                logging.warning(f"Ошибка при отправке урока {lesson} для пользователя: {user_id}")

            
            asyncio.create_task(send_reminder(bot, user_id, action, lesson["reminders"][0], delay=5))
            if len(lesson["reminders"]) > 1:
                asyncio.create_task(send_reminder(bot, user_id, action, lesson["reminders"][1], delay=30))

    elif type_ == "confirm":
        cursor.execute(""" 
        UPDATE progress SET viewed = TRUE, confirmed = TRUE WHERE user_id = ? AND step = ?""", (user_id, action))
        conn.commit()

        cursor.execute("""
        INSERT OR IGNORE INTO progress (user_id, step, viewed) VALUES (?, ?, ?)""", (user_id, action, True))
        conn.commit()

        next_lesson = LESSONS[action].get("next")
        if next_lesson:
            cursor.execute("""UPDATE users SET current_step = ? WHERE user_id = ?""", (next_lesson, user_id))
            conn.commit()

        await call.answer("Спасибо, что подтвердили просмотр!", show_alert=True)
        logging.warning(f"Пользователь: {user_id}, подтвердил просмотр урока {action}")

        
        if action == "lesson_3":
            final_lesson = LESSONS["final"]
            await bot.send_photo(chat_id=call.message.chat.id, photo=final_lesson["photo"], caption=final_lesson["text"].format(name=name))
            logging.warning(f"Для пользовател: {user_id} отправлен финальный урок")

        else:
            next_lesson = LESSONS[action].get("next")
            if next_lesson and next_lesson in LESSONS:
                lesson = LESSONS[next_lesson]
                asyncio.create_task(send_reminder(bot, user_id, next_lesson, lesson["reminders"][0], delay=5))
                
                if len(lesson["reminders"]) > 1:
                    asyncio.create_task(send_reminder(bot, user_id, next_lesson, LESSONS[next_lesson]["reminders"][1], delay=30))

                cursor.execute(""" 
                INSERT OR IGNORE INTO progress (user_id, step, viewed) VALUES (?, ?, ?)""", (user_id, next_lesson, True))  
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

def register_handlers(dp):
    dp.register_message_handler(cmd_start, commands="start")
    dp.register_callback_query_handler(cmd_admin, lambda c: c.data == "admin")