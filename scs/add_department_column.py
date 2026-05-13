import sqlite3

conn = sqlite3.connect("complaints.db")
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE complaints ADD COLUMN department TEXT DEFAULT 'Not Assigned'")
    print("Department column added successfully!")
except:
    print("Department column may already exist.")

conn.commit()
conn.close()