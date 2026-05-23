import sqlite3
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import check_password_hash

from database.db import get_db, init_db, seed_db, create_user, get_user_by_email
from database.queries import get_user_by_id, get_summary_stats, get_recent_transactions, get_category_breakdown

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"


def _fmt_date(iso):
    try:
        d = datetime.strptime(iso, "%Y-%m-%d")
        return f"{d.strftime('%b')} {d.day}, {d.year}"
    except Exception:
        return iso


def _first_of_month_n_ago(dt, n):
    m = dt.month - n
    y = dt.year
    if m < 1:
        m += 12
        y -= 1
    return f"{y:04d}-{m:02d}-01"


# ------------------------------------------------------------------ #
# Public routes                                                        #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Auth routes                                                          #
# ------------------------------------------------------------------ #

@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "POST":
        name             = request.form.get("name", "").strip()
        email            = request.form.get("email", "").strip()
        password         = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password or not confirm_password:
            flash("All fields are required.")
            return render_template("register.html")
        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template("register.html")
        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return render_template("register.html")

        try:
            create_user(name, email, password)
        except sqlite3.IntegrityError:
            flash("Email already registered.")
            return render_template("register.html")

        flash("Account created successfully! Please sign in.")
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("register.html")

    abort(405)


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("All fields are required.")
            return render_template("login.html")

        user = get_user_by_email(email)
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.")
            return render_template("login.html")

        session["user_id"]   = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("profile"))

    if request.method == "GET":
        return render_template("login.html")

    abort(405)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_id = session["user_id"]
    user    = get_user_by_id(user_id)

    start = request.args.get("start")
    end   = request.args.get("end")

    if start:
        try:
            datetime.strptime(start, "%Y-%m-%d")
        except ValueError:
            start = None
    if end:
        try:
            datetime.strptime(end, "%Y-%m-%d")
        except ValueError:
            end = None

    tx_limit = 1000 if (start or end) else 5

    filter_label = None
    if start or end:
        parts = [_fmt_date(start) if start else "beginning",
                 _fmt_date(end)   if end   else "today"]
        filter_label = f"{parts[0]} – {parts[1]}"

    today = datetime.today()
    today_str = today.strftime("%Y-%m-%d")
    presets = [
        ("This Month",    today.replace(day=1).strftime("%Y-%m-%d"), today_str),
        ("Last 3 Months", _first_of_month_n_ago(today, 3),          today_str),
        ("Last 6 Months", _first_of_month_n_ago(today, 6),          today_str),
    ]

    stats        = get_summary_stats(user_id, start_date=start, end_date=end)
    transactions = get_recent_transactions(user_id, limit=tx_limit, start_date=start, end_date=end)
    breakdown    = get_category_breakdown(user_id, start_date=start, end_date=end)

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        breakdown=breakdown,
        fmt_date=_fmt_date,
        start=start,
        end=end,
        filter_label=filter_label,
        presets=presets,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


with app.app_context():
    init_db()
    seed_db()

if __name__ == "__main__":
    app.run(debug=True, port=5001)
