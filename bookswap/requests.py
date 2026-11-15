"""Requesting a book (BS-31, story P04-US05).

A student taps Request on an Available book. The request is saved as Pending with
the student's name and the book, and shows in My Requests.
- Swap books: the student must offer one of their own Available books (criteria 6, 7).
- Sell books: the request shows the price and who to pay at handover (criterion 8).

Where requests are kept: the "Requests" tab of the Google Sheet when the secrets
are set; otherwise in memory until the app restarts (test mode), like listings.
"""

import json
from datetime import date

import pandas as pd
import streamlit as st

REQUEST_COLUMNS = ["Request ID", "Book ID", "Requester Name", "Request Date", "Status", "Offered Book ID"]
OPEN_STATUSES = ("Pending", "Accepted")  # a request that still counts (criterion 2)

MESSAGES = {
    "requested": "You have already requested this book.",
    "unavailable": "This book is already reserved by another student.",
    "own": "You can't request a book you listed.",
    "need_offer": "Choose one of your books to offer for this swap.",
    "no_books_to_offer": "List a book first to offer a swap.",
}


# ---------- Rules ----------

def request_state(book: pd.Series, user: str, requests: pd.DataFrame) -> str:
    """Which Request button the student sees (criteria 1 to 4).

    "own"         the student listed this book
    "unavailable" the book is Reserved or Exchanged
    "requested"   the student already has a Pending or Accepted request for it
    "available"   the student can request it
    """
    if str(book["Owner Name"]).strip().lower() == str(user).strip().lower():
        return "own"
    if str(book["Status"]) != "Available":
        return "unavailable"
    mine = requests[
        (requests["Book ID"] == book["Book ID"])
        & (requests["Requester Name"].str.lower() == str(user).lower())
        & (requests["Status"].isin(OPEN_STATUSES))
    ]
    return "requested" if not mine.empty else "available"


def books_to_offer(books: pd.DataFrame, user: str) -> pd.DataFrame:
    """The student's own Available books, for a swap offer (criterion 6)."""
    mine = books[(books["Owner Name"].str.lower() == str(user).lower()) & (books["Status"] == "Available")]
    return mine.reset_index(drop=True)


def check_request(book: pd.Series, user: str, requests: pd.DataFrame, books: pd.DataFrame,
                  offered_book_id: str | None = None) -> str | None:
    """Return an error message, or None if the request can be saved."""
    state = request_state(book, user, requests)
    if state != "available":
        return MESSAGES[state]
    if book["Exchange Type"] == "Swap":
        offer = books_to_offer(books, user)
        if offer.empty:
            return MESSAGES["no_books_to_offer"]
        if not offered_book_id or offered_book_id not in offer["Book ID"].tolist():
            return MESSAGES["need_offer"]
    return None


def pay_note(book: pd.Series) -> str:
    """Payment line for Sell books (criterion 8). Payment happens at handover, not in the app."""
    price = book["Price (Rs)"]
    amount = f"₹{int(price)}" if pd.notna(price) and str(price) != "" else "the price"
    return f"Pay {book['Owner Name']} {amount} at handover by UPI or cash"


def next_request_id(requests: pd.DataFrame) -> str:
    numbers = requests["Request ID"].astype(str).str.extract(r"(\d+)")[0].dropna().astype(int)
    return f"RQ-{(numbers.max() if len(numbers) else 0) + 1:03d}"


def make_request_row(request_id: str, book_id: str, user: str, offered_book_id: str | None = None,
                     today: date | None = None) -> list:
    """One row for the Requests sheet. Every new request starts as Pending (criterion 5)."""
    return [request_id, book_id, user, (today or date.today()).isoformat(), "Pending", offered_book_id or ""]


def my_requests(requests: pd.DataFrame, books: pd.DataFrame, user: str) -> pd.DataFrame:
    """The student's requests with their book details, newest first."""
    mine = requests[requests["Requester Name"].str.lower() == str(user).lower()].copy()
    if mine.empty:
        return mine
    mine["_order"] = mine["Request ID"].astype(str).str.extract(r"(\d+)")[0].astype(float)
    mine = mine.sort_values(["Request Date", "_order"], ascending=False).drop(columns="_order")
    book_details = books.rename(columns={"Status": "Book Status"})
    return mine.merge(book_details, on="Book ID", how="left").reset_index(drop=True)


# ---------- Reading and saving requests ----------

def _secret(key: str):
    try:
        return st.secrets[key]
    except Exception:
        return None


@st.cache_resource(show_spinner=False)
def _requests_worksheet():
    sheet_id, key_text = _secret("sheet_id"), _secret("service_account_json")
    if not sheet_id or not key_text:
        return None
    import gspread

    client = gspread.service_account_from_dict(json.loads(key_text))
    return client.open_by_key(sheet_id).worksheet("Requests")


@st.cache_resource(show_spinner=False)
def _temporary_requests() -> list:
    """Requests kept in memory when there is no Google Sheet (lost on restart)."""
    return []


def _worksheet_or_none():
    try:
        return _requests_worksheet()
    except Exception:
        return None


def is_permanent() -> bool:
    return _worksheet_or_none() is not None


def clean_requests(rows: list) -> pd.DataFrame:
    """Rows in REQUEST_COLUMNS order (by position, so a missing header cell is fine)."""
    padded = [(list(r) + [""] * len(REQUEST_COLUMNS))[: len(REQUEST_COLUMNS)] for r in rows]
    frame = pd.DataFrame(padded, columns=REQUEST_COLUMNS).fillna("").astype(str)
    frame = frame[frame["Request ID"].str.strip() != ""]
    return frame.reset_index(drop=True)


def load_requests() -> pd.DataFrame:
    worksheet = _worksheet_or_none()
    if worksheet is not None:
        return clean_requests(worksheet.get_all_values()[1:])
    return clean_requests(_temporary_requests())


def save_request(row: list) -> None:
    worksheet = _worksheet_or_none()
    if worksheet is not None:
        worksheet.append_row(row, value_input_option="RAW")
    else:
        _temporary_requests().append(row)
