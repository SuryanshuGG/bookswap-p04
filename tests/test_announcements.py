"""Tests for reading circle announcements (BS-49, story P04-US13)."""

from datetime import date, time

import pandas as pd

from bookswap import announcements as a
from bookswap import sheet_tabs

TODAY = date(2026, 11, 24)
USERS = pd.DataFrame([["Chandana", "Product Owner", ""], ["Krishna", "Builder", ""]],
                     columns=["Name", "Role", "College Email"])


def rows(*items):
    return sheet_tabs.to_frame([list(i) for i in items], a.COLUMNS)


def test_only_the_coordinator_can_post():  # criterion 5
    assert a.is_coordinator("Chandana", USERS)
    assert not a.is_coordinator("Krishna", USERS)
    assert a.check_post("Circle", date(2026, 11, 27), time(17, 0), "Library", False, TODAY) == a.MESSAGES["not_coordinator"]


def test_title_date_time_and_venue_are_required():  # criterion 3
    for args in [("", date(2026, 11, 27), time(17), "Library"), ("Circle", None, time(17), "Library"),
                 ("Circle", date(2026, 11, 27), None, "Library"), ("Circle", date(2026, 11, 27), time(17), "  ")]:
        assert a.check_post(*args, True, TODAY) == a.MESSAGES["missing"]
    assert a.check_post("Circle", date(2026, 11, 27), time(17), "Library", True, TODAY) is None


def test_past_date_is_refused():
    assert a.check_post("Circle", date(2026, 11, 20), time(17), "Library", True, TODAY) == a.MESSAGES["past"]


def test_past_events_hidden_and_soonest_first():  # criteria 2 and 4
    data = rows(["AN-001", "Old", "2026-11-20", "17:00", "Library", "", "Chandana", "x"],
                ["AN-002", "Later", "2026-11-28", "17:00", "Library", "", "Chandana", "x"],
                ["AN-003", "Sooner", "2026-11-25", "18:00", "Cafeteria", "", "Chandana", "x"],
                ["AN-004", "Today", "2026-11-24", "16:00", "Library", "", "Chandana", "x"])
    assert list(a.live(data, TODAY)["Title"]) == ["Today", "Sooner", "Later"]


def test_post_and_remove_in_test_mode():  # criterion 1
    store = sheet_tabs._memory(a.TAB)
    store.clear()
    assert a.post("Circle", a.today_ist(), time(17), "Library", "", "Chandana", USERS) is None
    assert a.post("Circle", a.today_ist(), time(17), "Library", "", "Krishna", USERS) == a.MESSAGES["not_coordinator"]
    assert list(a.load()["Title"]) == ["Circle"]
    assert a.remove("AN-001", "Krishna", USERS) == a.MESSAGES["not_coordinator"]
    assert a.remove("AN-001", "Chandana", USERS) is None
    assert a.load().empty
    store.clear()
