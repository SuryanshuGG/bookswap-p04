"""Checks for requesting a book (BS-31, story P04-US05)."""

from datetime import date

import pandas as pd

from bookswap.data import load_books
from bookswap.requests import (
    MESSAGES, books_to_offer, check_request, clean_requests, make_request_row, my_requests,
    next_request_id, pay_note, request_state,
)

BOOKS = load_books()


def book(book_id):
    return BOOKS[BOOKS["Book ID"] == book_id].iloc[0]


def requests_with(*rows):
    return clean_requests([list(r) for r in rows])


EMPTY = requests_with()
SWAP = book("BK-034")      # Atomic Habits, Swap, Suranjana, Available
SELL = book("BK-002")      # Positioning, Sell ₹450, Riya, Available
LEND = book("BK-009")      # Organizational Behavior, Lend, Riya, Available
RESERVED = book("BK-010")  # Work Rules!, Reserved
OWN = book("BK-004")       # Contagious, owned by Krishna


def test_available_book_can_be_requested_and_starts_pending():
    assert request_state(LEND, "Krishna", EMPTY) == "available"
    assert check_request(LEND, "Krishna", EMPTY, BOOKS) is None
    row = make_request_row("RQ-001", "BK-009", "Krishna", today=date(2026, 11, 15))
    assert row == ["RQ-001", "BK-009", "Krishna", "2026-11-15", "Pending", "", "", ""]


def test_second_request_is_blocked():
    existing = requests_with(["RQ-001", "BK-009", "Krishna", "2026-11-15", "Pending", ""])
    assert request_state(LEND, "Krishna", existing) == "requested"
    assert check_request(LEND, "Krishna", existing, BOOKS) == MESSAGES["requested"]


def test_declined_request_does_not_block_a_new_one():
    existing = requests_with(["RQ-001", "BK-009", "Krishna", "2026-11-15", "Declined", ""])
    assert request_state(LEND, "Krishna", existing) == "available"


def test_reserved_book_cannot_be_requested():
    assert request_state(RESERVED, "Krishna", EMPTY) == "unavailable"


def test_owner_cannot_request_own_book():
    assert request_state(OWN, "Krishna", EMPTY) == "own"


def test_swap_needs_one_of_my_available_books():
    offer = books_to_offer(BOOKS, "Krishna")
    assert len(offer) > 0 and (offer["Owner Name"] == "Krishna").all() and (offer["Status"] == "Available").all()
    assert check_request(SWAP, "Krishna", EMPTY, BOOKS) == MESSAGES["need_offer"]
    assert check_request(SWAP, "Krishna", EMPTY, BOOKS, offer.iloc[0]["Book ID"]) is None
    # Someone else's book can't be offered
    assert check_request(SWAP, "Krishna", EMPTY, BOOKS, "BK-001") == MESSAGES["need_offer"]


def test_swap_without_books_asks_to_list_first():
    assert books_to_offer(BOOKS, "Test Student 1").empty
    assert check_request(SWAP, "Test Student 1", EMPTY, BOOKS) == MESSAGES["no_books_to_offer"]


def test_sell_request_shows_price_and_who_to_pay():
    assert pay_note(SELL) == "Pay Riya ₹450 at handover by UPI or cash"


def test_my_requests_shows_only_mine_newest_first():
    reqs = requests_with(
        ["RQ-001", "BK-009", "Krishna", "2026-11-14", "Pending", ""],
        ["RQ-002", "BK-002", "Nandan", "2026-11-15", "Pending", ""],
        ["RQ-003", "BK-002", "Krishna", "2026-11-15", "Pending", ""],
    )
    mine = my_requests(reqs, BOOKS, "Krishna")
    assert mine["Request ID"].tolist() == ["RQ-003", "RQ-001"]
    assert mine.iloc[0]["Title"].startswith("Positioning")
    assert mine.iloc[0]["Status"] == "Pending" and mine.iloc[0]["Book Status"] == "Available"
    assert next_request_id(reqs) == "RQ-004"
