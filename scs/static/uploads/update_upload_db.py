import sqlite3

conn = sqlite3.connect("complaints.db")
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE complaints ADD COLUMN file_name TEXT")
except:
    print("Column may already exist")

conn.commit()
conn.close()

print("Upload column added!")
