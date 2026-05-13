import sqlite3

conn = sqlite3.connect("complaints.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT,
    department TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS complaints(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    complaint TEXT,
    status TEXT,
    department TEXT,
    level INTEGER DEFAULT 1,
    ticket_id TEXT,
    file_name TEXT,
    created_at TEXT,
    last_updated TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS notifications(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    message TEXT,
    time TEXT
)
""")

conn.commit()
conn.close()
print("Database Ready ✅")