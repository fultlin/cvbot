import sqlite3

conn = sqlite3.connect('analytics.db')
cursor = conn.cursor()

tables = ['users', 'progress', 'reminders']

for table in tables:
    print(f"Содержимое таблицы {table}:")
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    print()

conn.close()
