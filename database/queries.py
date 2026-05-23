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


def get_summary_stats(user_id, start_date=None, end_date=None):
    conn = get_db()
    try:
        conditions = ["user_id = ?"]
        params = [user_id]
        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        where_clause = " AND ".join(conditions)
        row = conn.execute(
            f"SELECT COALESCE(SUM(amount), 0.0) AS total_spent,"
            f" COUNT(*) AS transaction_count"
            f" FROM expenses WHERE {where_clause}",
            tuple(params),
        ).fetchone()
        top = conn.execute(
            f"SELECT category FROM expenses WHERE {where_clause}"
            f" GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
            tuple(params),
        ).fetchone()
        return {
            "total_spent": row["total_spent"],
            "transaction_count": row["transaction_count"],
            "top_category": top["category"] if top else "—",
        }
    finally:
        conn.close()


def get_recent_transactions(user_id, limit=10, start_date=None, end_date=None):
    conn = get_db()
    try:
        conditions = ["user_id = ?"]
        params = [user_id]
        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        params.append(limit)
        where_clause = " AND ".join(conditions)
        rows = conn.execute(
            f"SELECT date, description, category, amount"
            f" FROM expenses WHERE {where_clause}"
            f" ORDER BY date DESC, id DESC LIMIT ?",
            tuple(params),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_category_breakdown(user_id, start_date=None, end_date=None):
    conn = get_db()
    try:
        conditions = ["user_id = ?"]
        params = [user_id]
        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        where_clause = " AND ".join(conditions)
        rows = conn.execute(
            f"SELECT category AS name, SUM(amount) AS amount"
            f" FROM expenses WHERE {where_clause}"
            f" GROUP BY category ORDER BY amount DESC",
            tuple(params),
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
