import sqlite3

db = sqlite3.connect("complaints.db")

db.execute("""
UPDATE users
SET department='Water'
WHERE username='water_dept'
""")

db.execute("""
UPDATE users
SET department='IT'
WHERE username='it_dept'
""")

db.execute("""
UPDATE users
SET department='Electrical'
WHERE username='electrical_dept'
""")

db.execute("""
UPDATE users
SET department='HR'
WHERE username='hr_dept'
""")

db.execute("""
UPDATE users
SET department='Accounts'
WHERE username='accounts_dept'
""")

db.commit()
db.close()

print("Department users updated")