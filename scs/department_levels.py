import sqlite3
from werkzeug.security import generate_password_hash

db = sqlite3.connect("complaints.db")

departments = [
    ("water_level1","Water","+919059589588"),
    ("water_level2","Water","+917207842992"),
    ("water_supreme","Water","+918019282568"),

    ("it_level1","IT","+919182250004"),
    ("it_level2","IT","+919182250005"),
    ("it_supreme","IT","+919182250006"),

    ("electrical_level1","Electrical","+919182250007"),
    ("electrical_level2","Electrical","+919182250008"),
    ("electrical_supreme","Electrical","+919182250009"),

    ("hr_level1","HR","+919182250010"),
    ("hr_level2","HR","+919182250011"),
    ("hr_supreme","HR","+919182250012"),

    ("accounts_level1","Accounts","+919182250013"),
    ("accounts_level2","Accounts","+919182250014"),
    ("accounts_supreme","Accounts","+919182250015"),
]

for username,dept,phone in departments:
    # Update existing users to department role
    db.execute("""
    UPDATE users SET role='department', department=?, phone=? WHERE username=?
    """, (dept, phone, username))

    # If not exists, insert
    if db.total_changes == 0:
        db.execute("""
        INSERT INTO users(username,password,role,department,phone)
        VALUES (?,?,?,?,?)
        """,
        (
            username,
            generate_password_hash("123"),
            "department",
            dept,
            phone
        ))

db.commit()
db.close()

print("Department level users updated/created successfully")