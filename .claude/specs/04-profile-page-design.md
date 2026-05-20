# Spec: Profile Page Design

## Overview
The profile page is the first authenticated landing destination in Spendly. After logging in or registering, users are redirected to `/profile`, which displays their account information (name, email, member-since date) alongside a summary of their recorded expenses: total amount spent, number of transactions, and a per-category breakdown. The route is session-gated — unauthenticated visitors are redirected to `/login`. This step converts the existing stub into a fully rendered, styled page that establishes the visual language for all future authenticated views.

## Depends on
- **Step 1 — Database Setup:** `get_db()`, `users` table, `expenses` table
- **Step 2 — Registration:** user rows exist in the database; session stores `user_id` and `user_name`
- **Step 3 — Login and Logout:** session lifecycle is managed; `session["user_id"]` is the authoritative identity token

## Routes
- `GET /profile` — fetch user info and expense summary, render profile page — **logged-in only**

## Database changes
No new tables or columns. Two new query helper functions must be added to `database/db.py`:

- `get_user_by_id(user_id)` — returns a single row from `users` matching the given id, or `None`
- `get_expense_summary(user_id)` — returns a dict with:
  - `total` (REAL): sum of all `amount` values for this user, defaulting to `0.0`
  - `count` (INTEGER): number of expense rows
  - `by_category` (list of dicts): each entry has `category` (TEXT) and `subtotal` (REAL), ordered by `subtotal DESC`

All queries use `?` placeholders. No SQL in `app.py`.

## Templates
- **Create:** `templates/profile.html` — extends `base.html`; displays user info card and expense summary section
- **Modify:** none

## Files to change
- `app.py` — implement `GET /profile` route (currently returns a stub string)
- `database/db.py` — add `get_user_by_id()` and `get_expense_summary()` helper functions

## Files to create
- `templates/profile.html` — profile page template
- `static/css/profile.css` — page-specific styles (linked from `profile.html` only, not `base.html`)

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use `sqlite3` directly via `get_db()`
- Parameterised queries only — `?` placeholders, never f-strings in SQL
- Passwords are not displayed anywhere on this page
- Use CSS variables only — never hardcode hex values (use `var(--accent)`, `var(--ink)`, etc.)
- All templates extend `base.html`
- `abort(401)` if `session.get("user_id")` is not set — do not redirect silently
- `abort(404)` if `get_user_by_id()` returns `None` (session has a stale/invalid user id)
- DB helper functions live in `database/db.py` only — the route fetches data, passes it to the template, done
- `profile.css` must be linked via `{% block extra_css %}` or an equivalent block in `base.html` — if that block doesn't exist, add it

## Definition of done
- [ ] Visiting `/profile` while logged out returns a 401 response
- [ ] Visiting `/profile` while logged in renders `profile.html` with the correct user name and email visible in the page
- [ ] The member-since date displayed matches the `created_at` value stored for that user in the database
- [ ] Total spent and transaction count shown on the page match the actual rows in the `expenses` table for that user
- [ ] The per-category breakdown lists every category that has at least one expense, with the correct subtotal for each
- [ ] A user with zero expenses sees a zero total and an appropriate empty state message instead of a broken table
- [ ] All internal links use `url_for()` — no hardcoded URLs
- [ ] The page is visually consistent with the existing auth pages — uses the same font, colour variables, and card style
- [ ] `pytest` passes with no regressions
