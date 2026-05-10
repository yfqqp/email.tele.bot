import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    email TEXT
)
""")

conn.commit()

def get_user(user_id):
    cur.execute("SELECT email FROM users WHERE user_id=?", (user_id,))
    return cur.fetchone()

def set_user(user_id, email):
    if get_user(user_id):
        cur.execute("UPDATE users SET email=? WHERE user_id=?", (email, user_id))
    else:
        cur.execute("INSERT INTO users VALUES (?, ?)", (user_id, email))
    conn.commit()