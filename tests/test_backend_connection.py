"""
Unit tests for database/queries.py — spec 05: Backend Connection.

Covers all 8 cases from the spec's unit-test table.
"""

import pytest
import uuid

from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)


def _unique_email():
    return f"bc_{uuid.uuid4().hex[:8]}@example.com"


def _make_user(name="Test User"):
    from database.db import create_user
    return create_user(name, _unique_email(), "password123")


def _add_expenses(user_id, expenses):
    from database.db import get_db
    conn = get_db()
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description)"
        " VALUES (?, ?, ?, ?, ?)",
        [(user_id, *e) for e in expenses],
    )
    conn.commit()
    conn.close()


# ── get_user_by_id ────────────────────────────────────────────────────────────

def test_get_user_by_id_valid(app):
    user_id = _make_user("Alice")
    result = get_user_by_id(user_id)
    assert result is not None
    assert result["name"] == "Alice"
    assert "@" in result["email"]
    assert "member_since" in result
    assert result["member_since"] != ""


def test_get_user_by_id_nonexistent(app):
    result = get_user_by_id(999999)
    assert result is None


def test_get_user_by_id_member_since_format(app):
    user_id = _make_user("Bob")
    result = get_user_by_id(user_id)
    # Should be "Month YYYY" e.g. "May 2026" — not raw ISO
    parts = result["member_since"].split()
    assert len(parts) == 2
    assert parts[1].isdigit()


# ── get_summary_stats ─────────────────────────────────────────────────────────

def test_get_summary_stats_with_expenses(app):
    user_id = _make_user()
    _add_expenses(user_id, [
        (500.00, "Food",      "2026-05-01", "Lunch"),
        (300.00, "Transport", "2026-05-02", "Bus"),
        (200.00, "Food",      "2026-05-03", "Dinner"),
    ])
    result = get_summary_stats(user_id)
    assert result["total_spent"] == pytest.approx(1000.00)
    assert result["transaction_count"] == 3
    assert result["top_category"] == "Food"  # 500+200=700 > 300


def test_get_summary_stats_no_expenses(app):
    user_id = _make_user()
    result = get_summary_stats(user_id)
    assert result == {"total_spent": 0, "transaction_count": 0, "top_category": "—"}


# ── get_recent_transactions ───────────────────────────────────────────────────

def test_get_recent_transactions_with_expenses(app):
    user_id = _make_user()
    _add_expenses(user_id, [
        (100.00, "Food",      "2026-05-01", "Old"),
        (200.00, "Transport", "2026-05-03", "Newer"),
        (300.00, "Bills",     "2026-05-05", "Newest"),
    ])
    result = get_recent_transactions(user_id)
    assert len(result) == 3
    assert result[0]["description"] == "Newest"   # most recent first
    assert result[-1]["description"] == "Old"
    assert all(k in result[0] for k in ("date", "description", "category", "amount"))


def test_get_recent_transactions_no_expenses(app):
    user_id = _make_user()
    result = get_recent_transactions(user_id)
    assert result == []


def test_get_recent_transactions_respects_limit(app):
    user_id = _make_user()
    _add_expenses(user_id, [
        (10.0, "Food", f"2026-05-{i:02d}", f"E{i}") for i in range(1, 16)  # 15 expenses
    ])
    result = get_recent_transactions(user_id, limit=5)
    assert len(result) == 5
    result_default = get_recent_transactions(user_id)
    assert len(result_default) == 10  # default limit


# ── get_category_breakdown ────────────────────────────────────────────────────

def test_get_category_breakdown_with_expenses(app):
    user_id = _make_user()
    _add_expenses(user_id, [
        (600.00, "Food",      "2026-05-01", ""),
        (300.00, "Transport", "2026-05-02", ""),
        (100.00, "Health",    "2026-05-03", ""),
    ])
    result = get_category_breakdown(user_id)
    assert len(result) == 3
    assert result[0]["name"] == "Food"         # highest amount first
    assert result[0]["amount"] == pytest.approx(600.00)
    assert all(isinstance(item["pct"], int) for item in result)
    assert sum(item["pct"] for item in result) == 100


def test_get_category_breakdown_no_expenses(app):
    user_id = _make_user()
    result = get_category_breakdown(user_id)
    assert result == []


def test_get_category_breakdown_pct_sums_to_100(app):
    user_id = _make_user()
    # Amounts that produce messy percentages when rounded individually
    _add_expenses(user_id, [
        (333.33, "A", "2026-05-01", ""),
        (333.33, "B", "2026-05-02", ""),
        (333.34, "C", "2026-05-03", ""),
    ])
    result = get_category_breakdown(user_id)
    assert sum(item["pct"] for item in result) == 100
