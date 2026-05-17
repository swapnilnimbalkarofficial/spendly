# Plan: Step 1 — Database Setup

## Context

Spendly's `database/db.py` is currently a stub (comments only). All future steps (auth, expense CRUD) depend on a working SQLite layer. This plan implements the three required functions and wires them into `app.py` startup.

---

## Files to Change

- `expense-tracker/database/db.py` — full implementation (currently a stub)
- `expense-tracker/app.py` — add import and startup calls

## Files to Create

- None (per spec section 8)

---

## Implementation

### 1. `database/db.py`

Implement three functions using `sqlite3` (stdlib) and `werkzeug.security`:

**`get_db()`**
- Connect to `spendly.db` in project root (use `os.path.abspath` relative to `__file__` so it works regardless of working directory)
- Set `conn.row_factory = sqlite3.Row`
- Execute `PRAGMA foreign_keys = ON`
- Return connection

**`init_db()`**
- Call `get_db()` to get a connection
- `CREATE TABLE IF NOT EXISTS users` with columns: `id INTEGER PRIMARY KEY AUTOINCREMENT`, `name TEXT NOT NULL`, `email TEXT UNIQUE NOT NULL`, `password_hash TEXT NOT NULL`, `created_at TEXT DEFAULT (datetime('now'))`
- `CREATE TABLE IF NOT EXISTS expenses` with columns: `id INTEGER PRIMARY KEY AUTOINCREMENT`, `user_id INTEGER NOT NULL REFERENCES users(id)`, `amount REAL NOT NULL`, `category TEXT NOT NULL`, `date TEXT NOT NULL`, `description TEXT`, `created_at TEXT DEFAULT (datetime('now'))`
- `conn.commit()` then `conn.close()`

**`seed_db()`**
- Call `get_db()`
- Check `SELECT id FROM users LIMIT 1` — if row exists, close and return early (idempotent)
- Insert demo user: name=`Demo User`, email=`demo@spendly.com`, password=`generate_password_hash("demo123")`
- Fetch the new user's `id`
- Insert 8 sample expenses via `executemany` covering all 7 categories (Food×2, Transport, Bills, Health, Entertainment, Shopping, Other), with dates spread across May 2026 in `YYYY-MM-DD` format, amounts as REAL
- `conn.commit()` then `conn.close()`

All SQL uses `?` placeholders — no f-strings or string formatting in SQL.

---

### 2. `app.py`

Add one import line after the existing Flask import:
```python
from database.db import get_db, init_db, seed_db
```

Add startup block just before `if __name__ == "__main__":`:
```python
with app.app_context():
    init_db()
    seed_db()
```

No routes change. No new packages.

---

## Verification

1. Run `python app.py` from the `expense-tracker/` directory — app should start without errors on port 5001
2. Confirm `spendly.db` file is created next to `app.py`
3. Open the DB with `sqlite3 spendly.db` or a GUI tool and verify:
   - Both tables exist with correct columns and constraints
   - One user row: email `demo@spendly.com`, `password_hash` is not plaintext
   - Eight expense rows, all linked to that user, spanning all 7 categories
4. Run `python app.py` a second time — no duplicate rows, no errors
5. Run `pytest` — existing tests should pass
