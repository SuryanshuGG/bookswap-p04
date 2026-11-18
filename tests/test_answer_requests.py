"""Checks for Accept and Decline (BS-36) and My Listings (BS-56), story P04-US07."""

from datetime import date, timedelta

from bookswap.data import load_books
from bookswap.listings import check_edit, delete_change, edit_changes, pause_change, visible_books
from bookswap.requests import (
    MESSAGES, clean_requests, collect_note, owner_badge, plan_answer, requester_badge, requests_for_owner,
)

BOOKS = load_books()
TODAY = date(2026, 11, 18)


def book(book_id):
    return BOOKS[BOOKS["Book ID"] == book_id].iloc[0]


def reqs(*rows):
    return clean_requests([list(r) for r in rows])


# BK-034 Atomic Habits (Swap, Suranjana) · BK-009 Organizational Behavior (Lend, Riya) · BK-002 Positioning (Sell ₹450, Riya)
REQS = reqs(
    ["RQ-001", "BK-034", "Krishna", "2026-11-16", "Pending", "BK-025"],
    ["RQ-002", "BK-034", "Nandan", "2026-11-17", "Pending", "BK-005"],
    ["RQ-003", "BK-009", "Krishna", "2026-11-17", "Pending", ""],
    ["RQ-004", "BK-002", "Krishna", "2026-11-17", "Pending", ""],
)


def test_accept_reserves_book_and_declines_other_requests():
    error, changes, book_changes = plan_answer(REQS, BOOKS, "RQ-001", "Suranjana", accept=True, today=TODAY)
    assert error is None
    assert changes["RQ-001"]["Status"] == "Accepted"      # criterion 4
    assert changes["RQ-002"]["Status"] == "Declined"      # criterion 3
    assert book_changes == {"Status": "Reserved"}         # criterion 1


def test_decline_only_changes_that_request():
    error, changes, book_changes = plan_answer(REQS, BOOKS, "RQ-002", "Suranjana", accept=False, today=TODAY)
    assert error is None and changes == {"RQ-002": {"Status": "Declined", "Seen By Requester": ""}} and book_changes == {}


def test_only_the_owner_can_answer():
    error, _, _ = plan_answer(REQS, BOOKS, "RQ-001", "Krishna", accept=True, today=TODAY)
    assert error == MESSAGES["not_owner"]                 # criterion 5


def test_lend_needs_a_return_date_within_60_days():
    assert plan_answer(REQS, BOOKS, "RQ-003", "Riya", True, None, TODAY)[0] == MESSAGES["need_return_date"]
    assert plan_answer(REQS, BOOKS, "RQ-003", "Riya", True, TODAY + timedelta(days=61), TODAY)[0] == MESSAGES["bad_return_date"]
    assert plan_answer(REQS, BOOKS, "RQ-003", "Riya", True, TODAY, TODAY)[0] == MESSAGES["bad_return_date"]
    error, changes, _ = plan_answer(REQS, BOOKS, "RQ-003", "Riya", True, TODAY + timedelta(days=14), TODAY)
    assert error is None and changes["RQ-003"]["Return Date"] == "2026-12-02"   # criterion 6


def test_answered_request_cannot_be_answered_again():
    done = reqs(["RQ-001", "BK-034", "Krishna", "2026-11-16", "Accepted", "BK-025"])
    assert plan_answer(done, BOOKS, "RQ-001", "Suranjana", False, today=TODAY)[0] == MESSAGES["not_pending"]


def test_owner_sees_requests_on_own_books_and_sell_note():
    mine = requests_for_owner(REQS, BOOKS, "Riya")
    assert sorted(mine["Request ID"]) == ["RQ-003", "RQ-004"]
    assert collect_note(book("BK-002")) == "Collect ₹450 at handover by UPI or cash"


def test_badges():
    assert owner_badge(REQS, BOOKS, "Suranjana") == 2     # criterion 8, owner
    answered = reqs(["RQ-001", "BK-034", "Krishna", "2026-11-16", "Accepted", "BK-025", "", ""],
                    ["RQ-003", "BK-009", "Krishna", "2026-11-17", "Declined", "", "", "yes"])
    assert requester_badge(answered, "Krishna") == 1      # criterion 8, requester; seen ones don't count


def test_edit_listing_rules():
    own = book("BK-004")  # Contagious, Krishna, Available
    assert check_edit(own, "Krishna", "Good", "Sell", 200) == {}
    assert "price" in check_edit(own, "Krishna", "Good", "Sell", 0)
    assert "owner" in check_edit(own, "Riya", "Good", "Swap", None)
    assert edit_changes("Good", "Swap", 200) == {"Condition": "Good", "Exchange Type": "Swap", "Price (Rs)": None}


def test_pause_hides_book_and_resume_shows_it():
    own = book("BK-004")
    assert pause_change(own, "Krishna", has_pending=False) == (None, {"Status": "Paused"})
    paused = BOOKS.copy()
    paused.loc[paused["Book ID"] == "BK-004", "Status"] = "Paused"
    assert "BK-004" not in visible_books(paused)["Book ID"].tolist()
    assert pause_change(paused[paused["Book ID"] == "BK-004"].iloc[0], "Krishna", False) == (None, {"Status": "Available"})


def test_delete_blocked_while_requests_wait():
    own = book("BK-004")
    assert delete_change(own, "Krishna", has_pending=True)[0] == "Decline its pending requests first."
    assert delete_change(own, "Krishna", has_pending=False) == (None, {"Status": "Deleted"})
    assert delete_change(book("BK-010"), "Suryanshu", False)[0] is not None   # Reserved can't be deleted
