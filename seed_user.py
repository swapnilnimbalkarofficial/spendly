import random
import sys

from werkzeug.security import generate_password_hash

from database.db import get_db

FIRST_NAMES = [
    "Aarav", "Arjun", "Rohan", "Vikram", "Karan", "Aditya", "Nikhil", "Rahul",
    "Siddharth", "Manish", "Priya", "Sneha", "Anjali", "Pooja", "Deepika",
    "Kavya", "Meera", "Shreya", "Divya", "Ananya",
]
LAST_NAMES = [
    "Sharma", "Patel", "Verma", "Singh", "Kumar", "Gupta", "Joshi", "Mehta",
    "Nair", "Reddy", "Iyer", "Pillai", "Bose", "Das", "Chatterjee",
    "Malhotra", "Kapoor", "Shah", "Rao", "Mishra",
]

first  = random.choice(FIRST_NAMES)
last   = random.choice(LAST_NAMES)
name   = f"{first} {last}"
suffix = random.randint(10, 999)
email  = f"{first.lower()}.{last.lower()}{suffix}@gmail.com"

conn = get_db()
try:
    existing = conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        print("User already exists, skipping")
        sys.exit(0)

    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, generate_password_hash("password123")),
    )
    conn.commit()
    user = conn.execute("SELECT id, name, email FROM users WHERE email = ?", (email,)).fetchone()
    print(f"id   : {user['id']}")
    print(f"name : {user['name']}")
    print(f"email: {user['email']}")
finally:
    conn.close()
