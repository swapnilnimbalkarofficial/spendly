"""
Tests for GET /profile date filter feature — spec 06: Profile Page Date Filter.

Covers all definition-of-done items from the spec:
  1.  No params → all-time data, no active filter label
  2.  ?start&end → filters transactions, stats, and category breakdown
  3.  Only start → open-ended upper bound
  4.  Only end  → open-ended lower bound
  5.  Active filter label when either param is present
  6.  "Clear" link navigates to /profile with no params
  7.  Date inputs pre-filled after submit
  8.  Invalid date string silently ignored → all-time data
  9.  /profile while logged out → redirect to /login
  10. Preset quick-filters on the page: This Month, Last 3 Months, Last 6 Months
"""

import uuid
import pytest


# ── Helpers ──────────────────────────────────────────────────────────────────

def _unique_email():
    return f"filter_user_{uuid.uuid4().hex[:8]}@example.com"


def _make_user_with_expenses(app):
    """
    Create a fresh user with a controlled set of dated expenses and return
    (user_id, authenticated_client).

    Expenses:
      2026-05-01  Food        500.00  Groceries
      2026-05-03  Transport   200.00  Bus pass
      2026-05-05  Food        300.00  Restaurant
      2026-05-07  Health      150.00  Pharmacy
      2026-05-09  Bills       400.00  Water bill
      2026-05-11  Shopping    250.00  Clothes
      2026-05-13  Entertainment 100.00  Cinema
    Total (all-time): 1900.00 across 7 expenses / 6 categories
    Top category: Food (800.00)
    """
    from database.db import create_user, get_db

    email = _unique_email()
    user_id = create_user("Filter Tester", email, "password123")

    conn = get_db()
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description)"
        " VALUES (?, ?, ?, ?, ?)",
        [
            (user_id, 500.00, "Food",          "2026-05-01", "Groceries"),
            (user_id, 200.00, "Transport",     "2026-05-03", "Bus pass"),
            (user_id, 300.00, "Food",          "2026-05-05", "Restaurant"),
            (user_id, 150.00, "Health",        "2026-05-07", "Pharmacy"),
            (user_id, 400.00, "Bills",         "2026-05-09", "Water bill"),
            (user_id, 250.00, "Shopping",      "2026-05-11", "Clothes"),
            (user_id, 100.00, "Entertainment", "2026-05-13", "Cinema"),
        ],
    )
    conn.commit()
    conn.close()

    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_name"] = "Filter Tester"
    return user_id, client


# ── 9. Auth guard ─────────────────────────────────────────────────────────────

class TestAuthGuard:
    def test_profile_no_params_unauthenticated_redirects_to_login(self, client):
        response = client.get("/profile")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_profile_with_start_param_unauthenticated_redirects_to_login(self, client):
        response = client.get("/profile?start=2026-05-01")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_profile_with_end_param_unauthenticated_redirects_to_login(self, client):
        response = client.get("/profile?end=2026-05-31")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_profile_with_both_params_unauthenticated_redirects_to_login(self, client):
        response = client.get("/profile?start=2026-05-01&end=2026-05-31")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


# ── 1. No params — all-time data, no active filter label ──────────────────────

class TestNoFilterBaseline:
    def test_profile_no_params_returns_200(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile")
        assert response.status_code == 200, "Profile with no params should return 200"

    def test_profile_no_params_shows_all_time_total(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile")
        # All 7 expenses sum to 1900.00
        assert b"1,900.00" in response.data, "All-time total should be 1,900.00 with no filter"

    def test_profile_no_params_shows_correct_transaction_count(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile")
        html = response.data.decode()
        assert "7" in html, "All-time count should show 7 expenses"

    def test_profile_no_params_no_active_filter_label(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile")
        html = response.data.decode()
        # The active filter label must NOT be present when no params given
        assert "Showing:" not in html, "No active filter label should appear without params"

    def test_profile_no_params_shows_all_categories_in_breakdown(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile")
        for category in [b"Food", b"Transport", b"Health", b"Bills", b"Shopping", b"Entertainment"]:
            assert category in response.data, f"{category.decode()} should appear in all-time breakdown"


# ── Filter form UI elements always present ────────────────────────────────────

class TestFilterFormPresence:
    def test_filter_form_has_start_date_input(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile")
        html = response.data.decode()
        assert 'name="start"' in html, "Filter form must have a start date input named 'start'"

    def test_filter_form_has_end_date_input(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile")
        html = response.data.decode()
        assert 'name="end"' in html, "Filter form must have an end date input named 'end'"

    def test_filter_form_date_inputs_are_type_date(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile")
        html = response.data.decode()
        # Both start and end inputs must use type="date"
        assert 'type="date"' in html, "Date inputs must use type='date' (native browser date picker)"

    def test_filter_form_has_submit_button(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile")
        html = response.data.decode()
        # A submit button or input of type submit must exist
        has_submit = 'type="submit"' in html or "<button" in html
        assert has_submit, "Filter form must have a submit button"


# ── 10. Preset quick-filters ──────────────────────────────────────────────────

class TestPresetQuickFilters:
    def test_this_month_preset_present(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile")
        assert b"This Month" in response.data, "Page must include 'This Month' quick-filter preset"

    def test_last_3_months_preset_present(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile")
        assert b"Last 3 Months" in response.data, "Page must include 'Last 3 Months' quick-filter preset"

    def test_last_6_months_preset_present(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile")
        assert b"Last 6 Months" in response.data, "Page must include 'Last 6 Months' quick-filter preset"

    def test_presets_link_to_profile_route(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile")
        html = response.data.decode()
        # Presets must link to /profile with start/end query params
        assert "/profile?start=" in html, "Preset links must point to /profile with start= param"


# ── 6. Clear link ─────────────────────────────────────────────────────────────

class TestClearLink:
    def test_clear_link_present_when_filter_active(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?start=2026-05-01&end=2026-05-05")
        html = response.data.decode()
        # A "Clear" link must be present pointing to /profile with no query params
        assert "Clear" in html, "A 'Clear' link must appear when a date filter is active"

    def test_clear_link_href_is_bare_profile(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?start=2026-05-01&end=2026-05-05")
        html = response.data.decode()
        # The href must be /profile without query params
        assert 'href="/profile"' in html, "Clear link href must be /profile with no query params"

    def test_clear_link_is_navigable(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile", follow_redirects=True)
        assert response.status_code == 200, "Navigating to /profile (no params) must return 200"


# ── 2. Full date range filter — stats, transactions, breakdown ────────────────

class TestFullDateRangeFilter:
    def test_filtered_total_spent_correct(self, app):
        _, auth_client = _make_user_with_expenses(app)
        # Range 2026-05-01 to 2026-05-05: Food(500) + Transport(200) + Food(300) = 1000.00
        response = auth_client.get("/profile?start=2026-05-01&end=2026-05-05")
        assert response.status_code == 200
        assert b"1,000.00" in response.data, "Filtered total should be 1,000.00 for May 01–05"

    def test_filtered_transaction_count_correct(self, app):
        _, auth_client = _make_user_with_expenses(app)
        # Range 2026-05-01 to 2026-05-05: 3 expenses
        response = auth_client.get("/profile?start=2026-05-01&end=2026-05-05")
        html = response.data.decode()
        assert "3" in html, "Filtered count should be 3 for May 01–05"

    def test_filtered_top_category_correct(self, app):
        _, auth_client = _make_user_with_expenses(app)
        # Range 2026-05-01 to 2026-05-05: Food=800, Transport=200 → top=Food
        response = auth_client.get("/profile?start=2026-05-01&end=2026-05-05")
        assert b"Food" in response.data, "Top category should be Food for May 01–05"

    def test_filtered_transactions_list_shows_in_range_items(self, app):
        _, auth_client = _make_user_with_expenses(app)
        # Range 2026-05-01 to 2026-05-05: Groceries, Bus pass, Restaurant
        response = auth_client.get("/profile?start=2026-05-01&end=2026-05-05")
        assert b"Groceries" in response.data, "Groceries (May 01) should appear in filtered range"
        assert b"Bus pass" in response.data, "Bus pass (May 03) should appear in filtered range"
        assert b"Restaurant" in response.data, "Restaurant (May 05) should appear in filtered range"

    def test_filtered_transactions_list_hides_out_of_range_items(self, app):
        _, auth_client = _make_user_with_expenses(app)
        # Range 2026-05-01 to 2026-05-05: Pharmacy(May07), Water bill(May09) are outside
        response = auth_client.get("/profile?start=2026-05-01&end=2026-05-05")
        assert b"Pharmacy" not in response.data, "Pharmacy (May 07) must not appear in May 01–05 filter"
        assert b"Water bill" not in response.data, "Water bill (May 09) must not appear in May 01–05 filter"
        assert b"Clothes" not in response.data, "Clothes (May 11) must not appear in May 01–05 filter"
        assert b"Cinema" not in response.data, "Cinema (May 13) must not appear in May 01–05 filter"

    def test_filtered_category_breakdown_excludes_out_of_range_categories(self, app):
        _, auth_client = _make_user_with_expenses(app)
        # Range 2026-05-01 to 2026-05-05 has no Health, Bills, Shopping, Entertainment
        response = auth_client.get("/profile?start=2026-05-01&end=2026-05-05")
        html = response.data.decode()
        # Transport and Food appear in this range
        assert "Transport" in html, "Transport should be in breakdown for May 01–05"

    def test_filtered_boundary_dates_inclusive(self, app):
        _, auth_client = _make_user_with_expenses(app)
        # Boundary test: start=2026-05-07 end=2026-05-07 → exactly Pharmacy (150.00)
        response = auth_client.get("/profile?start=2026-05-07&end=2026-05-07")
        assert b"150.00" in response.data, "Boundary date expense (May 07) must be inclusive"
        assert b"Pharmacy" in response.data, "Pharmacy (exactly on boundary) must appear"


# ── 3. Only start provided — open-ended upper bound ──────────────────────────

class TestOnlyStartFilter:
    def test_only_start_returns_200(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?start=2026-05-07")
        assert response.status_code == 200

    def test_only_start_excludes_earlier_expenses(self, app):
        _, auth_client = _make_user_with_expenses(app)
        # start=2026-05-07: expenses before May 07 (Groceries, Bus pass, Restaurant) excluded
        response = auth_client.get("/profile?start=2026-05-07")
        assert b"Groceries" not in response.data, "Groceries (May 01) must not appear with start=May07"
        assert b"Bus pass" not in response.data, "Bus pass (May 03) must not appear with start=May07"
        assert b"Restaurant" not in response.data, "Restaurant (May 05) must not appear with start=May07"

    def test_only_start_includes_later_expenses(self, app):
        _, auth_client = _make_user_with_expenses(app)
        # start=2026-05-07: Pharmacy(May07), Water bill(May09), Clothes(May11), Cinema(May13) included
        response = auth_client.get("/profile?start=2026-05-07")
        assert b"Pharmacy" in response.data, "Pharmacy (May 07) must appear with start=May07"
        assert b"Water bill" in response.data, "Water bill (May 09) must appear with start=May07"
        assert b"Cinema" in response.data, "Cinema (May 13) must appear with start=May07"

    def test_only_start_shows_active_filter_label(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?start=2026-05-07")
        html = response.data.decode()
        assert "Showing:" in html, "Active filter label must appear when only start is provided"

    def test_only_start_correct_total(self, app):
        _, auth_client = _make_user_with_expenses(app)
        # start=2026-05-07: Pharmacy(150) + Water bill(400) + Clothes(250) + Cinema(100) = 900.00
        response = auth_client.get("/profile?start=2026-05-07")
        assert b"900.00" in response.data, "Total from May 07 onward should be 900.00"


# ── 4. Only end provided — open-ended lower bound ────────────────────────────

class TestOnlyEndFilter:
    def test_only_end_returns_200(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?end=2026-05-05")
        assert response.status_code == 200

    def test_only_end_excludes_later_expenses(self, app):
        _, auth_client = _make_user_with_expenses(app)
        # end=2026-05-05: expenses after May 05 excluded
        response = auth_client.get("/profile?end=2026-05-05")
        assert b"Pharmacy" not in response.data, "Pharmacy (May 07) must not appear with end=May05"
        assert b"Water bill" not in response.data, "Water bill (May 09) must not appear with end=May05"
        assert b"Cinema" not in response.data, "Cinema (May 13) must not appear with end=May05"

    def test_only_end_includes_earlier_expenses(self, app):
        _, auth_client = _make_user_with_expenses(app)
        # end=2026-05-05: Groceries(May01), Bus pass(May03), Restaurant(May05) included
        response = auth_client.get("/profile?end=2026-05-05")
        assert b"Groceries" in response.data, "Groceries (May 01) must appear with end=May05"
        assert b"Bus pass" in response.data, "Bus pass (May 03) must appear with end=May05"
        assert b"Restaurant" in response.data, "Restaurant (May 05) must appear with end=May05"

    def test_only_end_shows_active_filter_label(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?end=2026-05-05")
        html = response.data.decode()
        assert "Showing:" in html, "Active filter label must appear when only end is provided"

    def test_only_end_correct_total(self, app):
        _, auth_client = _make_user_with_expenses(app)
        # end=2026-05-05: Food(500) + Transport(200) + Food(300) = 1000.00
        response = auth_client.get("/profile?end=2026-05-05")
        assert b"1,000.00" in response.data, "Total up to May 05 should be 1,000.00"


# ── 5. Active filter label ────────────────────────────────────────────────────

class TestActiveFilterLabel:
    def test_label_present_with_both_params(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?start=2026-05-01&end=2026-05-13")
        assert b"Showing:" in response.data, "Active filter label must appear when both params provided"

    def test_label_present_with_only_start(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?start=2026-05-01")
        assert b"Showing:" in response.data, "Active filter label must appear when only start is present"

    def test_label_present_with_only_end(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?end=2026-05-13")
        assert b"Showing:" in response.data, "Active filter label must appear when only end is present"

    def test_label_absent_with_no_params(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile")
        html = response.data.decode()
        assert "Showing:" not in html, "Active filter label must NOT appear when no params provided"

    def test_label_contains_start_date(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?start=2026-05-01&end=2026-05-13")
        html = response.data.decode()
        # Label should show the start date in human-readable form (e.g. "May 1, 2026")
        assert "2026" in html, "Active filter label should reference the year"
        assert "May" in html, "Active filter label should reference the month"

    def test_label_contains_end_date(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?start=2026-05-01&end=2026-05-13")
        html = response.data.decode()
        # The range string must mention something about the end boundary
        assert "Showing:" in html
        showing_idx = html.index("Showing:")
        # There should be a dash/separator in the label
        label_region = html[showing_idx: showing_idx + 200]
        assert "–" in label_region or "-" in label_region or "to" in label_region, (
            "Active filter label must show date range with a separator"
        )


# ── 7. Date inputs pre-filled after submit ────────────────────────────────────

class TestInputsPrefilled:
    def test_start_input_prefilled_with_filter_value(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?start=2026-05-03&end=2026-05-09")
        html = response.data.decode()
        assert "2026-05-03" in html, "Start date input must be pre-filled with the current filter value"

    def test_end_input_prefilled_with_filter_value(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?start=2026-05-03&end=2026-05-09")
        html = response.data.decode()
        assert "2026-05-09" in html, "End date input must be pre-filled with the current filter value"

    def test_only_start_prefills_start_input(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?start=2026-05-05")
        html = response.data.decode()
        assert "2026-05-05" in html, "Start date input must be pre-filled when only start is given"

    def test_only_end_prefills_end_input(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?end=2026-05-11")
        html = response.data.decode()
        assert "2026-05-11" in html, "End date input must be pre-filled when only end is given"

    def test_no_params_inputs_are_empty(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile")
        html = response.data.decode()
        # Neither a fixed date value should be forced into empty inputs
        assert "value=\"2026-05-" not in html, (
            "Date inputs must be empty (no value) when no filter params are given"
        )


# ── 8. Invalid date strings silently ignored ──────────────────────────────────

class TestInvalidDateHandling:
    def test_invalid_start_returns_200(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?start=not-a-date")
        assert response.status_code == 200, "Invalid start date must not crash — should return 200"

    def test_invalid_end_returns_200(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?end=foobar")
        assert response.status_code == 200, "Invalid end date must not crash — should return 200"

    def test_both_invalid_returns_200(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?start=bad&end=also-bad")
        assert response.status_code == 200, "Both invalid dates must not crash — should return 200"

    def test_invalid_start_shows_all_time_data(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?start=not-a-date")
        # All-time total is 1900.00 — invalid filter must not truncate data
        assert b"1,900.00" in response.data, (
            "Invalid start date must be silently ignored; all-time total must appear"
        )

    def test_invalid_end_shows_all_time_data(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?end=foobar")
        assert b"1,900.00" in response.data, (
            "Invalid end date must be silently ignored; all-time total must appear"
        )

    def test_both_invalid_shows_all_time_data(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?start=bad&end=also-bad")
        assert b"1,900.00" in response.data, (
            "Both invalid dates silently ignored; all-time total must appear"
        )

    def test_invalid_start_no_active_filter_label(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?start=not-a-date")
        html = response.data.decode()
        assert "Showing:" not in html, (
            "Invalid start param must be ignored; no active filter label should appear"
        )

    def test_invalid_end_no_active_filter_label(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?end=foobar")
        html = response.data.decode()
        assert "Showing:" not in html, (
            "Invalid end param must be ignored; no active filter label should appear"
        )

    def test_partial_invalid_valid_start_invalid_end(self, app):
        _, auth_client = _make_user_with_expenses(app)
        # Valid start, invalid end: should apply start filter only
        response = auth_client.get("/profile?start=2026-05-07&end=not-a-date")
        assert response.status_code == 200
        html = response.data.decode()
        # Filter label appears because start is valid
        assert "Showing:" in html, (
            "Active filter label must appear when start is valid even if end is invalid"
        )
        # Expenses before May 07 should NOT appear
        assert b"Groceries" not in response.data, (
            "Valid start must still be applied when end is invalid"
        )

    def test_partial_invalid_invalid_start_valid_end(self, app):
        _, auth_client = _make_user_with_expenses(app)
        # Invalid start, valid end: should apply end filter only
        response = auth_client.get("/profile?start=not-a-date&end=2026-05-05")
        assert response.status_code == 200
        html = response.data.decode()
        # Filter label appears because end is valid
        assert "Showing:" in html, (
            "Active filter label must appear when end is valid even if start is invalid"
        )
        # Expenses after May 05 should NOT appear
        assert b"Cinema" not in response.data, (
            "Valid end must still be applied when start is invalid"
        )

    @pytest.mark.parametrize("bad_value", [
        "2026-13-01",   # month 13 does not exist
        "2026-00-01",   # month 0 does not exist
        "2026-05-32",   # day 32 does not exist
        "05-01-2026",   # wrong format (MM-DD-YYYY)
        "2026/05/01",   # wrong separator
        "20260501",     # no separators
        "",             # empty string (treated as absent by Flask)
    ])
    def test_various_invalid_start_formats_return_200(self, app, bad_value):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get(f"/profile?start={bad_value}")
        assert response.status_code == 200, (
            f"Invalid start='{bad_value}' must not crash the page"
        )


# ── Transactions limit behavior ───────────────────────────────────────────────

class TestTransactionLimit:
    def test_filter_active_shows_all_matching_transactions(self, app):
        """When a date filter is active, all matching transactions (more than 5) must be shown."""
        from database.db import create_user, get_db

        email = _unique_email()
        user_id = create_user("Limit Test", email, "password123")
        conn = get_db()
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description)"
            " VALUES (?, ?, ?, ?, ?)",
            [
                (user_id, 10.0, "Food", f"2026-05-{i:02d}", f"Item {i}")
                for i in range(1, 9)  # 8 expenses on May 01–08
            ],
        )
        conn.commit()
        conn.close()

        auth_client = app.test_client()
        with auth_client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["user_name"] = "Limit Test"

        # Filter covers all 8 expenses — all 8 should appear (not capped at 5)
        response = auth_client.get("/profile?start=2026-05-01&end=2026-05-08")
        html = response.data.decode()
        for i in range(1, 9):
            assert f"Item {i}" in html, (
                f"Item {i} must appear when date filter covers all expenses (limit removed)"
            )

    def test_no_filter_limits_recent_transactions_to_five(self, app):
        """Without a date filter, only the 5 most recent transactions should appear."""
        from database.db import create_user, get_db

        email = _unique_email()
        user_id = create_user("Limit NoFilter", email, "password123")
        conn = get_db()
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description)"
            " VALUES (?, ?, ?, ?, ?)",
            [
                (user_id, 10.0, "Food", f"2026-05-{i:02d}", f"NF Item {i}")
                for i in range(1, 9)  # 8 expenses; oldest is May 01 and May 02
            ],
        )
        conn.commit()
        conn.close()

        auth_client = app.test_client()
        with auth_client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["user_name"] = "Limit NoFilter"

        response = auth_client.get("/profile")
        html = response.data.decode()

        # Most recent 5 are May 04–08 (NF Item 4 through NF Item 8)
        for i in range(4, 9):
            assert f"NF Item {i}" in html, (
                f"NF Item {i} (within top-5 recency) must appear without filter"
            )
        # Oldest 3 (May 01, 02, 03) must NOT appear
        for i in range(1, 4):
            assert f"NF Item {i}" not in html, (
                f"NF Item {i} (outside top-5 recency) must NOT appear without filter"
            )


# ── Empty result set under filter ─────────────────────────────────────────────

class TestEmptyFilterResult:
    def test_filter_matching_no_expenses_returns_200(self, app):
        _, auth_client = _make_user_with_expenses(app)
        # Date range in the distant future — no expenses match
        response = auth_client.get("/profile?start=2030-01-01&end=2030-12-31")
        assert response.status_code == 200, (
            "A filter that matches no expenses must still return 200"
        )

    def test_filter_matching_no_expenses_shows_zero_total(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?start=2030-01-01&end=2030-12-31")
        assert b"0.00" in response.data, (
            "When filter matches no expenses, total should display as 0.00"
        )

    def test_filter_matching_no_expenses_shows_no_transactions_message(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?start=2030-01-01&end=2030-12-31")
        html = response.data.decode()
        # The page must gracefully indicate no matching transactions
        has_empty_state = (
            "No transactions" in html
            or "no expenses" in html.lower()
            or "0.00" in html
        )
        assert has_empty_state, (
            "Empty filter result must show a no-transactions state or zero total"
        )

    def test_filter_matching_no_expenses_active_label_still_shown(self, app):
        _, auth_client = _make_user_with_expenses(app)
        response = auth_client.get("/profile?start=2030-01-01&end=2030-12-31")
        html = response.data.decode()
        assert "Showing:" in html, (
            "Active filter label must appear even when no matching expenses found"
        )
