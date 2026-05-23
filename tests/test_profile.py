"""
Tests for GET /profile — spec 05: Backend Routes for Profile Page.

Covers all 10 definition-of-done items from the spec.
"""

import pytest


# ── 1. Unauthenticated redirect ──────────────────────────────────────────────

def test_profile_redirects_unauthenticated(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_redirect_follows_to_login(client):
    response = client.get("/profile", follow_redirects=True)
    assert response.status_code == 200
    assert b"Sign in" in response.data or b"password" in response.data


# ── 2. Correct name and email displayed ──────────────────────────────────────

def test_profile_shows_user_name(new_user):
    _, _email, client = new_user
    response = client.get("/profile")
    assert response.status_code == 200
    assert b"Jane Doe" in response.data


def test_profile_shows_user_email(new_user):
    _, email, client = new_user
    response = client.get("/profile")
    assert email.encode() in response.data


# ── 3. Member-since date is human-readable ───────────────────────────────────

def test_profile_shows_member_since(new_user):
    _, _email, client = new_user
    response = client.get("/profile")
    assert b"Member since" in response.data
    # Date should not be raw ISO format like "2026-05-21T..."
    assert b"T" not in response.data or b"Member since 20" not in response.data


# ── 4 & 5. Total spend and expense count ─────────────────────────────────────

def test_profile_total_spend(user_with_expenses):
    _, client = user_with_expenses
    response = client.get("/profile")
    assert response.status_code == 200
    # 500 + 200 + 300 + 100 + 150 + 250 = 1500.00
    assert b"1,500.00" in response.data


def test_profile_expense_count(user_with_expenses):
    _, client = user_with_expenses
    response = client.get("/profile")
    assert b"6" in response.data


# ── 6. Top category ──────────────────────────────────────────────────────────

def test_profile_top_category(user_with_expenses):
    _, client = user_with_expenses
    response = client.get("/profile")
    # Food: 500+300=800 is the highest category
    assert b"Food" in response.data


# ── 7. Recent transactions — up to 5, most recent first ─────────────────────

def test_profile_recent_transactions_present(user_with_expenses):
    _, client = user_with_expenses
    response = client.get("/profile")
    assert b"Recent Transactions" in response.data
    # Electricity (May 6) is the most recent — within the limit-5 window
    assert b"Electricity" in response.data


def test_profile_recent_transactions_limit_five(app):
    """User with 7 expenses should see only 5 in recent transactions."""
    from database.db import create_user, get_db
    user_id = create_user("limit@example.com", "limit@example.com", "pass1234")
    conn = get_db()
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description)"
        " VALUES (?, ?, ?, ?, ?)",
        [
            (user_id, 10.0, "Food", f"2026-05-{i:02d}", f"Expense {i}")
            for i in range(1, 8)  # 7 expenses
        ],
    )
    conn.commit()
    conn.close()

    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_name"] = "Limit User"

    response = client.get("/profile")
    # The 7th (oldest) expense should NOT appear; only 5 most recent
    assert b"Expense 1" not in response.data
    assert b"Expense 2" not in response.data
    assert b"Expense 7" in response.data  # most recent is present


def test_profile_recent_transactions_most_recent_first(user_with_expenses):
    _, client = user_with_expenses
    response = client.get("/profile")
    html = response.data.decode()
    # "Electricity" (May 6) should appear before "Bus pass" (May 2)
    # Both are within the limit-5 window; Groceries (May 1) is excluded
    assert html.index("Electricity") < html.index("Bus pass")


# ── 8. Category breakdown ────────────────────────────────────────────────────

def test_profile_category_breakdown_present(user_with_expenses):
    _, client = user_with_expenses
    response = client.get("/profile")
    assert b"Spending by Category" in response.data
    assert b"Transport" in response.data
    assert b"Entertainment" in response.data
    assert b"Health" in response.data
    assert b"Bills" in response.data


# ── 9. Zero-expense user ─────────────────────────────────────────────────────

def test_profile_zero_expenses_top_category_dash(new_user):
    _, _email, client = new_user
    response = client.get("/profile")
    assert "—" in response.data.decode() or "&mdash;" in response.data.decode()


def test_profile_zero_expenses_total_zero(new_user):
    _, _email, client = new_user
    response = client.get("/profile")
    assert b"0.00" in response.data


def test_profile_zero_expenses_no_transactions_message(new_user):
    _, _email, client = new_user
    response = client.get("/profile")
    assert b"No transactions yet" in response.data


# ── 10. Demo user with 8 seed expenses ───────────────────────────────────────

def test_demo_user_profile(app):
    from database.db import get_user_by_email
    demo = get_user_by_email("demo@spendly.com")
    assert demo is not None, "seed_db() must have run; demo user not found"

    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = demo["id"]
        sess["user_name"] = demo["name"]

    response = client.get("/profile")
    assert response.status_code == 200
    assert b"Demo User" in response.data
    # 8 seeded expenses across 7 categories
    assert b"Food" in response.data
    assert b"Transport" in response.data
    assert b"Bills" in response.data
    assert b"Health" in response.data
    assert b"Entertainment" in response.data
    assert b"Shopping" in response.data
    assert b"Other" in response.data
