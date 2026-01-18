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
    pdf_file TEXT
)
""")
try:
    c.execute("ALTER TABLE prescriptions ADD COLUMN pdf_file TEXT")
    print("pdf_file column added successfully")
except sqlite3.OperationalError:
    print("pdf_file column already exists")

conn.commit()
conn.close()
