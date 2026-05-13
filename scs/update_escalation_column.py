import sqlite3

conn = sqlite3.connect("complaints.db")
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE complaints ADD COLUMN escalation_message TEXT")
except:
    print("Already exists")

conn.commit()
conn.close()