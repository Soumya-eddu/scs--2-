import sqlite3

db = sqlite3.connect("complaints.db")

# ADMIN PHONE
db.execute("""
UPDATE users
SET phone='+919182253957'
WHERE role='admin'
""")

# WATER DEPARTMENT
db.execute("""
UPDATE users
SET phone='+919059589588'
WHERE username='water_dept'
""")

# IT DEPARTMENT
db.execute("""
UPDATE users
SET phone='+919182250001'
WHERE username='it_dept'
""")

# ELECTRICAL DEPARTMENT
db.execute("""
UPDATE users
SET phone='+919182250002'
WHERE username='electrical_dept'
""")

# HR DEPARTMENT
db.execute("""
UPDATE users
SET phone='+919182250003'
WHERE username='hr_dept'
""")

# ACCOUNTS DEPARTMENT
db.execute("""
UPDATE users
SET phone='+919182250004'
WHERE username='accounts_dept'
""")

db.commit()
db.close()

print("✅ Admin and department phone numbers updated successfully")