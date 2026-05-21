from datetime import datetime

from database.db import get_db


def get_user_by_id(user_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if row is None:
            return None
        try:
            dt = datetime.fromisoformat(row["created_at"])
            member_since = dt.strftime("%B %Y")
        except Exception:
            member_since = row["created_at"]
        return {"name": row["name"], "email": row["email"], "member_since": member_since}
    finally:
        conn.close()


def get_summary_stats(user_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0.0) AS total_spent,"
            " COUNT(*) AS transaction_count"
            " FROM expenses WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        top = conn.execute(
            "SELECT category FROM expenses WHERE user_id = ?"
            " GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        return {
            "total_spent": row["total_spent"],
            "transaction_count": row["transaction_count"],
            "top_category": top["category"] if top else "—",
        }
    finally:
        conn.close()


def get_recent_transactions(user_id, limit=10):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT date, description, category, amount"
            " FROM expenses WHERE user_id = ?"
            " ORDER BY date DESC, id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_category_breakdown(user_id):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT category AS name, SUM(amount) AS amount"
            " FROM expenses WHERE user_id = ?"
            " GROUP BY category ORDER BY amount DESC",
            (user_id,),
        ).fetchall()
        if not rows:
            return []
        total = sum(r["amount"] for r in rows)
        pcts = [round(r["amount"] / total * 100) for r in rows]
        pcts[0] += 100 - sum(pcts)
        return [
            {"name": r["name"], "amount": r["amount"], "pct": p}
            for r, p in zip(rows, pcts)
        ]
    finally:
        conn.close()
