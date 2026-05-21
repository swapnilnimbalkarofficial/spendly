import os
import sqlite3

from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "spendly.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            description TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()
    if conn.execute("SELECT id FROM users LIMIT 1").fetchone():
        conn.close()
        return

    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
    )
    conn.commit()

    user_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
    ).fetchone()["id"]

    sample_expenses = [
        (user_id, 250.00,  "Food",          "2026-05-01", "Grocery shopping"),
        (user_id, 120.00,  "Transport",     "2026-05-03", "Cab to office"),
        (user_id, 1500.00, "Bills",         "2026-05-05", "Electricity bill"),
        (user_id, 800.00,  "Health",        "2026-05-07", "Doctor consultation"),
        (user_id, 350.00,  "Entertainment", "2026-05-10", "Movie tickets"),
        (user_id, 600.00,  "Shopping",      "2026-05-12", "Clothing purchase"),
        (user_id, 180.00,  "Other",         "2026-05-14", "Miscellaneous"),
        (user_id, 90.00,   "Food",          "2026-05-16", "Lunch"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        sample_expenses,
    )
    conn.commit()
    conn.close()


def get_user_by_id(user_id):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()


def get_expense_summary(user_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0.0) AS total, COUNT(*) AS count"
            " FROM expenses WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        by_category = conn.execute(
            "SELECT category, SUM(amount) AS subtotal"
            " FROM expenses WHERE user_id = ?"
            " GROUP BY category ORDER BY subtotal DESC",
            (user_id,),
        ).fetchall()
        return {
            "total": row["total"],
            "count": row["count"],
            "by_category": [(r["category"], r["subtotal"]) for r in by_category],
        }
    finally:
        conn.close()


def get_recent_expenses(user_id, limit=5):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT id, date, description, category, amount"
            " FROM expenses WHERE user_id = ?"
            " ORDER BY date DESC, id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
    finally:
        conn.close()


def create_user(name, email, password):
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()
