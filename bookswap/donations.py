"""Donate a book to the department library (BS-51, story P04-US14).

Acceptance criteria:
1. When I choose Donate, the coordinator sees it in a donation list.
2. When the coordinator marks it Received, the listing closes.
3. While a book is marked for donation, no one can request, borrow, swap or buy it.
4. The donation list shows the donor's name, the book title and the date offered.
5. Until it is Received, I can withdraw my donation.

Book Status: Available -> Donated (still visible, can't be requested) -> Closed (hidden),
or back to Available on withdraw. Donations are logged in a "Donations" tab.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd

from bookswap import sheet_tabs

TAB = "Donations"
COLUMNS = ["Donation ID", "Book ID", "Book Title", "Donor", "Offered On", "Status", "Updated"]

MESSAGES = {
    "not_owner": "Only the book's owner can donate it.",
    "not_available": "Only an Available book can be donated.",
    "pending": "Decline its pending requests first.",
    "offered": "Thank you! The coordinator will collect it for the department library.",
    "withdrawn": "Donation withdrawn. Your book is Available again.",
    "received": "Marked Received. The listing is now closed.",
    "not_coordinator": "Only the literary club coordinator can mark donations Received.",
    "not_open": "This donation is no longer open.",
    "unavailable_to_others": "Donated to the department library. It can't be requested.",
}


def today_ist() -> date:
    return datetime.now(ZoneInfo("Asia/Kolkata")).date()


def check_donate(book: pd.Series, user: str, has_pending: bool) -> str | None:
    if str(book["Owner Name"]).lower() != str(user).lower():
        return MESSAGES["not_owner"]
    if book["Status"] != "Available":
        return MESSAGES["not_available"]
    if has_pending:
        return MESSAGES["pending"]
    return None


def open_donation(donations: pd.DataFrame, book_id: str):
    """The book's Offered donation as a dict, or None."""
    if donations.empty:
        return None
    rows = donations[(donations["Book ID"] == book_id) & (donations["Status"] == "Offered")]
    return rows.iloc[-1].to_dict() if not rows.empty else None


def coordinator_list(donations: pd.DataFrame) -> pd.DataFrame:
    """Open donations, oldest first, for the coordinator (criteria 1 and 4)."""
    if donations.empty:
        return donations
    return donations[donations["Status"] == "Offered"].sort_values("Offered On").reset_index(drop=True)


# ---------- Storage (each returns (error, message, book_changes)) ----------

def load() -> pd.DataFrame:
    return sheet_tabs.load(TAB, COLUMNS)


def donate(book: pd.Series, user: str, has_pending: bool):
    error = check_donate(book, user, has_pending)
    if error:
        return error, "", {}
    donations = load()
    sheet_tabs.append(TAB, COLUMNS, [sheet_tabs.next_id(donations, "Donation ID", "DN"), book["Book ID"], book["Title"],
                                     user, today_ist().isoformat(), "Offered", today_ist().isoformat()])
    return None, MESSAGES["offered"], {"Status": "Donated"}


def withdraw(book: pd.Series, user: str):
    """Criterion 5: the donor takes it back before it is Received."""
    if str(book["Owner Name"]).lower() != str(user).lower():
        return MESSAGES["not_owner"], "", {}
    donation = open_donation(load(), book["Book ID"])
    if donation is None:
        return MESSAGES["not_open"], "", {}
    sheet_tabs.update(TAB, COLUMNS, donation["Donation ID"], {"Status": "Withdrawn", "Updated": today_ist().isoformat()})
    return None, MESSAGES["withdrawn"], {"Status": "Available"}


def mark_received(donation_id: str, is_coordinator: bool):
    """Criterion 2: the coordinator collects it and the listing closes."""
    if not is_coordinator:
        return MESSAGES["not_coordinator"], "", {}
    donations = load()
    row = donations[donations["Donation ID"] == donation_id]
    if row.empty or row.iloc[0]["Status"] != "Offered":
        return MESSAGES["not_open"], "", {}
    sheet_tabs.update(TAB, COLUMNS, donation_id, {"Status": "Received", "Updated": today_ist().isoformat()})
    return None, MESSAGES["received"], {"Status": "Closed"}


def is_permanent() -> bool:
    return sheet_tabs.is_permanent(TAB, COLUMNS)
