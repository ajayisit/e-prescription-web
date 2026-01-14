import sqlite3

conn = sqlite3.connect("patients.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS prescriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name TEXT,
    age TEXT,
    gender TEXT,
    diagnosis TEXT,
    medicines TEXT,
    date TEXT
)
""")

conn.commit()
conn.close()
