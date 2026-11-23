"""Tests for the campus handover rules (BS-39, story P04-US08)."""

from datetime import date, datetime, time

import pandas as pd

from bookswap import handover as h
from bookswap import sheet_tabs

NOW = datetime(2026, 11, 24, 10, 0)
BOOK = pd.Series({"Book ID": "BK-001", "Title": "Atomic Habits", "Owner Name": "Riya", "Exchange Type": "Swap",
                  "Price (Rs)": "", "Status": "Reserved"})
REQ = pd.Series({"Request ID": "RQ-001", "Book ID": "BK-001", "Requester Name": "Krishna", "Status": "Accepted",
                 "Offered Book ID": "BK-009", "Return Date": ""})
PLAN = {"Request ID": "RQ-001", "Point": "Library entrance", "Date": "2026-11-26", "Time": "16:30",
        "Owner Done": "", "Requester Done": "", "Paid": "", "Returned": ""}


def test_only_approved_points():  # criterion 1
    assert h.check_schedule("Parking lot", date(2026, 11, 26), time(16, 30), NOW) == h.MESSAGES["bad_point"]
    assert h.check_schedule("Library entrance", date(2026, 11, 26), time(16, 30), NOW) is None


def test_only_future_time_within_hours():  # criterion 3
    assert h.check_schedule("Cafeteria", date(2026, 11, 24), time(9, 30), NOW) == h.MESSAGES["past"]
    assert h.check_schedule("Cafeteria", date(2026, 11, 26), time(21, 0), NOW) == h.MESSAGES["hours"]
    assert h.check_schedule("Cafeteria", None, time(10), NOW) == h.MESSAGES["missing"]


def test_one_confirmation_keeps_reserved_two_make_exchanged():  # criteria 2 and 4
    error, changes, book, offered = h.plan_confirm(PLAN, REQ, BOOK, "Krishna")
    assert error is None and changes == {"Requester Done": "yes"} and book == {} and offered == {}
    after = {**PLAN, "Requester Done": "yes"}
    error, changes, book, offered = h.plan_confirm(after, REQ, BOOK, "Riya")
    assert changes == {"Owner Done": "yes"} and book == {"Status": "Exchanged"}
    assert offered == {"Status": "Exchanged"}  # the swapped book changes hands too


def test_confirm_rules():
    assert h.plan_confirm(PLAN, REQ, BOOK, "Nandan")[0] == h.MESSAGES["not_party"]
    assert h.plan_confirm(None, REQ, BOOK, "Riya")[0] == h.MESSAGES["not_scheduled"]
    assert h.plan_confirm({**PLAN, "Owner Done": "yes"}, REQ, BOOK, "Riya")[0] == h.MESSAGES["already_done"]


def test_sell_marked_paid_with_amount():  # criterion 6
    sell = BOOK.copy(); sell["Exchange Type"] = "Sell"; sell["Price (Rs)"] = "450"
    done = {**PLAN, "Owner Done": "yes", "Requester Done": "yes"}
    assert h.plan_paid(PLAN, REQ, sell, "Riya")[0] == h.MESSAGES["not_exchanged"]
    assert h.plan_paid(done, REQ, sell, "Krishna")[0] == h.MESSAGES["owner_only"]
    assert h.plan_paid(done, REQ, sell, "Riya") == (None, {"Paid": "yes", "Paid Amount": "450"})


def test_lend_reminder_overdue_and_returned():  # criteria 7 and 8
    lend = BOOK.copy(); lend["Exchange Type"] = "Lend"
    req = REQ.copy(); req["Return Date"] = "2026-11-26"; req["Offered Book ID"] = ""
    done = {**PLAN, "Owner Done": "yes", "Requester Done": "yes"}
    assert h.lend_status(req, done, date(2026, 11, 20)) == "On loan"
    assert h.lend_status(req, done, date(2026, 11, 24)) == "Due soon"
    assert h.lend_status(req, done, date(2026, 11, 27)) == "Overdue"
    assert h.plan_returned(done, req, lend, "Riya") == (None, {"Returned": "yes"}, {"Status": "Available"})
    assert h.lend_status(req, {**done, "Returned": "yes"}, date(2026, 11, 27)) == "Returned"
    requests = pd.DataFrame([req]); books = pd.DataFrame([lend])
    handovers = sheet_tabs.to_frame([[done.get(c, "") for c in h.COLUMNS]], h.COLUMNS)
    assert h.reminders(requests, books, handovers, "Krishna", date(2026, 11, 24)) == [
        "Reminder: return Atomic Habits to Riya by 26 Nov."]


def test_short_messages_only():  # criterion 9
    assert h.check_message("  ") == h.MESSAGES["empty_message"]
    assert h.check_message("x" * 201) == h.MESSAGES["long_message"]
    assert h.check_message("See you at the library at 4:30") is None
