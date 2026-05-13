import sqlite3

conn = sqlite3.connect("complaints.db")
cur = conn.cursor()

def add_column(column_sql):
    try:
        cur.execute(column_sql)
        print("Column added.")
    except:
        print("Column already exists.")

# Add missing columns
add_column("ALTER TABLE complaints ADD COLUMN level INTEGER DEFAULT 1")
add_column("ALTER TABLE complaints ADD COLUMN created_at TEXT")
add_column("ALTER TABLE complaints ADD COLUMN last_updated TEXT")
add_column("ALTER TABLE complaints ADD COLUMN escalation_message TEXT")

conn.commit()
conn.close()

print("Database updated successfully!")