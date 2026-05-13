import sqlite3

conn = sqlite3.connect("complaints.db")
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE users ADD COLUMN phone TEXT")
except:
    print("Phone column already exists")

conn.commit()
conn.close()

print("Phone column added")

