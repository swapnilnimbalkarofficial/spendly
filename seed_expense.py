import random
import sys
from datetime import date

from database.db import get_db

CATEGORIES = ["Food", "Transport", "Entertainment", "Shopping", "Health", "Bills", "Other"]

DESCRIPTIONS = {
    "Food":          ["Grocery shopping", "Lunch", "Dinner out", "Coffee", "Street food"],
    "Transport":     ["Cab to office", "Auto rickshaw", "Metro card recharge", "Petrol", "Bus ticket"],
    "Entertainment": ["Movie tickets", "OTT subscription", "Concert tickets", "Gaming"],
    "Shopping":      ["Clothing purchase", "Electronics", "Home decor", "Books", "Shoes"],
    "Health":        ["Doctor consultation", "Medicine", "Gym membership", "Lab tests"],
    "Bills":         ["Electricity bill", "Internet bill", "Mobile recharge", "Water bill"],
    "Other":         ["Miscellaneous", "Gift", "Donation", "Stationery"],
}

conn = get_db()
try:
    users = conn.execute("SELECT id FROM users").fetchall()
    if not users:
        print("No users found, run seed_user.py first")
        sys.exit(0)

    user_id  = random.choice(users)["id"]
    amount   = round(random.uniform(100, 5000), 2)
    category = random.choice(CATEGORIES)
    desc     = random.choice(DESCRIPTIONS[category])
    today    = date.today().isoformat()

    duplicate = conn.execute(
        "SELECT 1 FROM expenses WHERE user_id=? AND amount=? AND category=? AND date=?",
        (user_id, amount, category, today),
    ).fetchone()
    if duplicate:
        print("Expense already exists, skipping")
        sys.exit(0)

    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, category, today, desc),
    )
    conn.commit()
    expense = conn.execute(
        "SELECT id, user_id, amount, category FROM expenses WHERE user_id=? AND amount=? AND category=? AND date=?",
        (user_id, amount, category, today),
    ).fetchone()
    print(f"expense id: {expense['id']}")
    print(f"user id   : {expense['user_id']}")
    print(f"amount    : {expense['amount']}")
    print(f"category  : {expense['category']}")
finally:
    conn.close()
