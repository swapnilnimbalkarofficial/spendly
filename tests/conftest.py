import os
import tempfile
import uuid
import pytest

# Patch DB_PATH BEFORE importing app — app.py calls init_db() + seed_db()
# at module level, so the path must be redirected before the first import.
import database.db as db_module

_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)
db_module.DB_PATH = _db_path

from app import app as flask_app  # noqa: E402 — intentional late import


@pytest.fixture(scope="session")
def app():
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"
    yield flask_app
    if os.path.exists(_db_path):
        os.unlink(_db_path)


@pytest.fixture
def client(app):
    return app.test_client()


def _unique_email():
    return f"user_{uuid.uuid4().hex[:8]}@example.com"


@pytest.fixture
def new_user(app):
    """Create a fresh user with no expenses and return (user_id, email, client)."""
    from database.db import create_user
    email = _unique_email()
    user_id = create_user("Jane Doe", email, "password123")
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_name"] = "Jane Doe"
    return user_id, email, client


@pytest.fixture
def user_with_expenses(app):
    """Create a user with a known set of expenses and return (user_id, client)."""
    from database.db import create_user, get_db
    user_id = create_user("John Smith", _unique_email(), "password123")

    conn = get_db()
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description)"
        " VALUES (?, ?, ?, ?, ?)",
        [
            (user_id, 500.00, "Food",          "2026-05-01", "Groceries"),
            (user_id, 200.00, "Transport",     "2026-05-02", "Bus pass"),
            (user_id, 300.00, "Food",          "2026-05-03", "Restaurant"),
            (user_id, 100.00, "Entertainment", "2026-05-04", "Cinema"),
            (user_id, 150.00, "Health",        "2026-05-05", "Pharmacy"),
            (user_id, 250.00, "Bills",         "2026-05-06", "Electricity"),
        ],
    )
    conn.commit()
    conn.close()

    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_name"] = "John Smith"
    return user_id, client
