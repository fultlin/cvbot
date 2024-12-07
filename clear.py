import sqlite3

conn = sqlite3.connect('analytics.db')
cursor = conn.cursor()

def clear_database():
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM progress")
    conn.commit()
    print("Database cleared successfully.")

clear_database()

conn.close()
