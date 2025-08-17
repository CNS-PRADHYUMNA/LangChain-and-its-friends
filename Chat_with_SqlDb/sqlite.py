import sqlite3
from faker import Faker

fake = Faker()

# Create (or connect to) local SQLite database file
conn = sqlite3.connect("emp.db")
cursor = conn.cursor()

# Create Employees table (if not exists)
cursor.execute("""
CREATE TABLE IF NOT EXISTS Employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    salary REAL,
    hire_date TEXT
)
""")

# Insert 100 fake records
for i in range(100):
    cursor.execute("""
        INSERT INTO Employees (first_name, last_name, email, salary, hire_date)
        VALUES (?, ?, ?, ?, ?)
    """, (
        fake.first_name(),
        fake.last_name(),
        fake.email(),
        round(fake.random_number(digits=5), 2),
        fake.date_between(start_date='-2y', end_date='today').isoformat()
    ))


conn.commit()
conn.close()


conn = sqlite3.connect("emp.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM Employees LIMIT 10;")
for row in cursor.fetchall():
    print(row)

conn.close()
