# Spec: Login and Logout

## Overview

Step 3 upgrades the `/login` route from a stub that always returns "Invalid email or password" into a real credential-checking flow. It looks up the submitted email in the `users` table, verifies the password with `werkzeug`, and on success writes `user_id` and `user_name` into the Flask session so subsequent routes can identify who is logged in. The `/logout` route already clears the session and redirects to landing — it just needs the error-display pattern aligned with the rest of the app. `base.html` is also updated so the navbar shows context-aware links (Sign in / Get started when logged out; Profile / Sign out when logged in).

---

## Depends on

- Step 01 — Database Setup (`users` table, `get_db()`)
- Step 02 — Registration (`create_user()`, password hashing pattern)

---

## Routes

- `GET /login` — render login form — public
- `POST /login` — verify credentials, set session, redirect to `/profile` on success — public
- `GET /logout` — clear session, redirect to `/` — public (already exists, align error pattern)

---

## Database changes

No new tables or columns. A new read-only DB helper is needed:

- `get_user_by_email(email)` — queries `users` by email, returns the full row as `sqlite3.Row` or `None` if not found. Used by the login route to look up the user before checking the password.

---

## Templates

- **Modify:** `templates/login.html`
  - Fix form `action` from `/login` to `{{ url_for('login') }}`
  - Replace `{% if error %}{{ error }}{% endif %}` block with `get_flashed_messages()` pattern (same as `register.html`)
  - Display the success flash from registration ("Account created successfully! Please sign in.") — works automatically once the flash pattern is in place

- **Modify:** `templates/base.html`
  - Update `<div class="nav-links">` to show different links based on session:
    - Logged out: "Sign in" + "Get started" (current behaviour)
    - Logged in: user's name or "Profile" link + "Sign out" link

---

## Files to change

- `database/db.py` — add `get_user_by_email(email)`, add `check_password_hash` to werkzeug import
- `app.py` — upgrade `/login` route (verify credentials, set session, flash, redirect); align `/logout`
- `templates/login.html` — fix action URL, switch to flash messages
- `templates/base.html` — context-aware navbar

---

## Files to create

None.

---

## New dependencies

No new dependencies. Uses:
- `werkzeug.security.check_password_hash` — already installed, just not yet imported
- Flask `session` — already imported in `app.py`

---

## Rules for implementation

- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()`
- Parameterised queries only — `?` placeholders, never f-strings in SQL
- Passwords checked with `werkzeug.security.check_password_hash` — never compare plaintext
- On failed login (wrong email or wrong password) always flash the same generic message: "Invalid email or password." — never reveal which field was wrong
- Session keys to set on success: `session["user_id"]`, `session["user_name"]`
- On success redirect to `url_for("profile")` — never hardcode `/profile`
- `abort(405)` for unsupported methods on `/login`
- All DB logic stays in `database/db.py` — no inline SQL in routes
- All templates extend `base.html`
- Use CSS variables — never hardcode hex values
- Use `url_for()` for every internal link — never hardcode URLs

---

## Definition of done

- [ ] `GET /login` renders the login form without errors
- [ ] Submitting valid credentials sets `session["user_id"]` and `session["user_name"]` and redirects to `/profile`
- [ ] Submitting wrong password stays on `/login` with flash "Invalid email or password."
- [ ] Submitting an email that doesn't exist stays on `/login` with flash "Invalid email or password."
- [ ] Submitting empty fields stays on `/login` with a validation flash message
- [ ] Visiting `/logout` clears the session and redirects to the landing page
- [ ] After logout, visiting `/login` shows the form with no session data
- [ ] Navbar shows "Sign in" / "Get started" when logged out, and profile name / "Sign out" when logged in
- [ ] The success flash from registration ("Account created successfully! Please sign in.") is visible on the login page after registering
