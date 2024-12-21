import sqlite3

conn = sqlite3.connect("analytics.db")
cursor = conn.cursor()

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        current_step TEXT
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
            f"ID Пользователя: <a href='tg://user?id={entry[0]}'>{entry[0]}</a>,\nШаг: {entry[1]},\nПоказан: {'Да' if entry[2]==1 else 'нет'},\nПройден: {'Да' if entry[3]==1 else 'нет'},\nВремя: {entry[4]}\n---------------\n"
        )
    return progress_info

def insert_user(user_id, username, first_name, last_name):
    cursor.execute("""
    INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
    VALUES (?, ?, ?, ?)
    """, (user_id, username, first_name, last_name))
    conn.commit()

def update_user_step(user_id, step):
    cursor.execute("""
    UPDATE users
    SET current_step = ?
    WHERE user_id = ?
    """, (step, user_id))
    conn.commit()

def insert_progress(user_id, step, viewed=True):
    cursor.execute("""
    INSERT OR IGNORE INTO progress (user_id, step, viewed)
    VALUES (?, ?, ?)
    """, (user_id, step, viewed))
    conn.commit()

def update_progress(user_id, step, viewed=True, confirmed=True):
    cursor.execute("""
    UPDATE progress
    SET viewed = ?, confirmed = ?
    WHERE user_id = ? AND step = ?
    """, (viewed, confirmed, user_id, step))
    conn.commit()
