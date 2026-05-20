# Spec: Profile Page Design

## Overview
Step 4 upgrades the `/profile` stub into a fully-rendered profile page that shows the logged-in user's account details and a summary of their spending. The page displays the user's name, email, and member-since date alongside a stats bar (total amount spent, total number of expenses, and a per-category breakdown). The route is login-protected — unauthenticated visitors are redirected to `/login`. This is the first authenticated page in the app and establishes the visual pattern that the dashboard and expense pages will inherit.

## Depends on
- Step 01 — Database Setup (`users` and `expenses` tables, `get_db()`)
- Step 02 — Registration (user rows exist in `users`)
- Step 03 — Login and Logout (session keys `user_id` and `user_name` set on login)

## Routes
- `GET /profile` — render the profile page for the logged-in user — logged-in only (redirect to `/login` if not authenticated)

## Database changes
No new tables or columns. Two new read-only DB helpers are needed in `database/db.py`:

- `get_user_by_id(user_id)` — queries `users` by primary key, returns the full row as `sqlite3.Row` or `None`. Used by the profile route to fetch name, email, and `created_at`.
- `get_expense_summary(user_id)` — returns a dict with:
  - `total` — sum of all `amount` values for this user (REAL, default `0.0` if no expenses)
  - `count` — total number of expense rows for this user (INTEGER)
  - `by_category` — list of `(category, subtotal)` tuples ordered by subtotal descending

## Templates
- **Create:** `templates/profile.html`
  - Extends `base.html`
  - Profile header: user's name, email, member since date (formatted from `created_at`)
  - Stats row: Total Spent (₹ formatted to 2 decimal places), Number of Expenses
  - Category breakdown: list showing each category with its subtotal and a proportional fill bar (width = subtotal / max_subtotal × 100%)
  - "Add Expense" call-to-action button linking to `url_for('add_expense')` (stub — that is fine for this step)

## Files to change
- `app.py` — replace stub `return "Profile page — coming in Step 4"` with a login guard, data fetch via the two new helpers, and `render_template("profile.html", ...)`
- `database/db.py` — add `get_user_by_id(user_id)` and `get_expense_summary(user_id)` helpers

## Files to create
- `templates/profile.html` — profile page template
- `static/css/profile.css` — page-specific styles (linked via `{% block head %}` in the template)

## New dependencies
No new dependencies. Uses only stdlib `sqlite3`, Flask, and existing CSS variables.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only
- Parameterised queries only — `?` placeholders, never f-strings in SQL
- Passwords hashed with werkzeug (no auth changes in this step)
- Use CSS variables — never hardcode hex values (use `var(--accent)`, `var(--ink)`, etc.)
- All templates extend `base.html`
- Login guard: if `session.get("user_id")` is falsy, `return redirect(url_for("login"))`
- All DB logic stays in `database/db.py` — no inline SQL in route functions
- Currency amounts displayed in ₹ (INR) — format as `₹{value:,.2f}` in the template
- Dates displayed in human-readable form (e.g. "May 1, 2026") — not raw ISO strings; use a Jinja2 filter or pass a pre-formatted string from the route
- Category bar widths calculated as percentage of the largest category subtotal — use inline `style="width: X%"` on the bar fill element; guard against division by zero when no expenses exist
- Use `url_for()` for every internal link — never hardcode paths

## Definition of done
- [ ] `GET /profile` redirects to `/login` when the user is not logged in
- [ ] `GET /profile` renders without errors when logged in with the demo account
- [ ] Page displays the logged-in user's name, email, and formatted member-since date
- [ ] Total amount spent is shown formatted in ₹ (INR)
- [ ] Total expense count is shown
- [ ] Each spending category appears with its subtotal and a proportional fill bar
- [ ] "Add Expense" button is visible and links to the add-expense route (stub message is acceptable)
- [ ] Visiting `/profile` after logout redirects to `/login` — no 500 error
- [ ] All colours in `profile.css` use CSS variables — no hardcoded hex values