import sqlite3

db = sqlite3.connect("complaints.db")
cursor = db.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN department TEXT")
    print("Department column added to users table")
except:
    print("Department column already exists")

db.commit()
db.close()