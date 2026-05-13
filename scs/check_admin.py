import sqlite3

db = sqlite3.connect("complaints.db")

db.execute("""
UPDATE users
SET phone='+919182253957'
WHERE role='admin'
""")

db.commit()
db.close()

print("Admin phone updated successfully")