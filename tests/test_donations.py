"""Tests for donating a book (BS-51, story P04-US14)."""

import pandas as pd

from bookswap import donations as d
from bookswap import requests as book_requests
from bookswap import sheet_tabs

BOOK = pd.Series({"Book ID": "BK-030", "Title": "The Personal MBA", "Owner Name": "Riya", "Status": "Available",
                  "Exchange Type": "Swap"})


def test_only_owner_and_only_available_without_pending():
    assert d.check_donate(BOOK, "Krishna", False) == d.MESSAGES["not_owner"]
    assert d.check_donate(BOOK.replace("Available", "Reserved"), "Riya", False) == d.MESSAGES["not_available"]
    assert d.check_donate(BOOK, "Riya", True) == d.MESSAGES["pending"]
    assert d.check_donate(BOOK, "Riya", False) is None


def test_donate_list_withdraw_and_receive():  # criteria 1, 2, 4 and 5
    store = sheet_tabs._memory(d.TAB); store.clear()
    error, _, changes = d.donate(BOOK, "Riya", False)
    assert error is None and changes == {"Status": "Donated"}
    listed = d.coordinator_list(d.load())
    assert list(listed.columns[:5]) == ["Donation ID", "Book ID", "Book Title", "Donor", "Offered On"]
    assert listed.iloc[0]["Donor"] == "Riya" and listed.iloc[0]["Book Title"] == "The Personal MBA"
    donated = BOOK.copy(); donated["Status"] = "Donated"
    assert d.withdraw(donated, "Riya")[2] == {"Status": "Available"}
    assert d.coordinator_list(d.load()).empty
    d.donate(BOOK, "Riya", False)
    donation_id = d.coordinator_list(d.load()).iloc[0]["Donation ID"]
    assert d.mark_received(donation_id, False)[0] == d.MESSAGES["not_coordinator"]
    assert d.mark_received(donation_id, True)[2] == {"Status": "Closed"}
    assert d.withdraw(donated, "Riya")[0] == d.MESSAGES["not_open"]  # too late once Received
    store.clear()


def test_donated_book_cannot_be_requested():  # criterion 3
    donated = BOOK.copy(); donated["Status"] = "Donated"
    empty = pd.DataFrame(columns=book_requests.REQUEST_COLUMNS)
    assert book_requests.request_state(donated, "Krishna", empty) == "unavailable"
