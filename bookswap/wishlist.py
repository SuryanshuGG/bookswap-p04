"""Wishlist (BS-42, story P04-US10): save a book you can't find, and see when someone lists it.

Rules (acceptance criteria):
1. A book that isn't listed can be saved under my account.
2. When a matching book is listed later, my wishlist marks it Now Available.
3. Adding a book that's already on my wishlist tells me it's already saved.
4. A removed book no longer appears.
5. I only see my own wishlist.
6. A badge on Wishlist counts my books that are Now Available.

Where wishes are kept: a "Wishlist" tab in the Google Sheet (made automatically the
first time), or in memory when the Sheet isn't connected (test mode).
"""

import json
import re
from datetime import date

import pandas as pd
import streamlit as st

WISHLIST_COLUMNS = ["Wish ID", "Student", "Title", "Author", "Date Added"]

MESSAGES = {
    "saved": "Saved to your wishlist. It will show Now Available when someone lists it.",
    "duplicate": "This book is already on your wishlist.",
    "no_title": "Enter the book's title.",
    "removed": "Removed from your wishlist.",
}


# ---------- Rules (no storage, so they can be unit tested) ----------

def normalise(text) -> str:
    """Lower case, letters and digits only, single spaces: 'Atomic  Habits!' -> 'atomic habits'."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(text).lower()).split())


def titles_match(wished: str, listed: str) -> bool:
    """Same title, or one contains the other (so 'Atomic Habits' matches
    'Atomic Habits: Tiny Changes...'). Very short words don't count as a match."""
    a, b = normalise(wished), normalise(listed)
    if not a or not b:
        return False
    if a == b:
        return True
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    return len(shorter) >= 4 and f" {shorter} " in f" {longer} "


def my_wishes(wishes: pd.DataFrame, student: str) -> pd.DataFrame:
    """Only this student's wishes, newest first (criterion 5)."""
    if wishes.empty:
        return wishes
    mine = wishes[wishes["Student"].str.lower() == str(student).lower()]
    return mine.iloc[::-1].reset_index(drop=True)


def check_add(title: str, wishes: pd.DataFrame, student: str) -> str | None:
    """Error message, or None if the book can be saved (criteria 1 and 3)."""
    if not normalise(title):
        return MESSAGES["no_title"]
    for existing in my_wishes(wishes, student)["Title"] if not wishes.empty else []:
        if normalise(existing) == normalise(title):
            return MESSAGES["duplicate"]
    return None


def next_wish_id(wishes: pd.DataFrame) -> str:
    numbers = wishes["Wish ID"].str.extract(r"(\d+)")[0].dropna().astype(int) if not wishes.empty else []
    return f"W-{(max(numbers) if len(numbers) else 0) + 1:03d}"


def make_wish_row(wish_id: str, student: str, title: str, author: str = "", today: date | None = None) -> list:
    return [wish_id, student.strip(), title.strip(), author.strip(), (today or date.today()).isoformat()]


def matching_books(title: str, books: pd.DataFrame, student: str) -> pd.DataFrame:
    """Available books, listed by someone else, whose title matches the wish (criterion 2)."""
    if books.empty:
        return books
    available = books[(books["Status"] == "Available")
                      & (books["Owner Name"].str.lower() != str(student).lower())]
    return available[available["Title"].apply(lambda listed: titles_match(title, listed))]


def with_matches(mine: pd.DataFrame, books: pd.DataFrame, student: str) -> pd.DataFrame:
    """Adds 'Now Available' (True/False) and 'Match IDs' (the matching Book IDs)."""
    mine = mine.copy()
    ids = [list(matching_books(t, books, student)["Book ID"]) for t in mine["Title"]] if not mine.empty else []
    mine["Match IDs"] = ids
    mine["Now Available"] = [bool(i) for i in ids]
    return mine


def badge_count(wishes: pd.DataFrame, books: pd.DataFrame, student: str) -> int:
    """How many of my wishes are Now Available (criterion 6)."""
    mine = my_wishes(wishes, student)
    if mine.empty:
        return 0
    return int(with_matches(mine, books, student)["Now Available"].sum())


# ---------- Reading and saving wishes ----------

def _secret(key: str):
    try:
        return st.secrets[key]
    except Exception:
        return None


@st.cache_resource(show_spinner=False)
def _wishlist_worksheet():
    """The Wishlist tab of the Google Sheet; made with its header row if it doesn't exist yet."""
    sheet_id, key_text = _secret("sheet_id"), _secret("service_account_json")
    if not sheet_id or not key_text:
        raise LookupError("Google Sheet secrets are not set")
    import gspread

    sheet = gspread.service_account_from_dict(json.loads(key_text)).open_by_key(sheet_id)
    try:
        return sheet.worksheet("Wishlist")
    except gspread.WorksheetNotFound:
        worksheet = sheet.add_worksheet("Wishlist", rows=200, cols=len(WISHLIST_COLUMNS))
        worksheet.append_row(WISHLIST_COLUMNS, value_input_option="RAW")
        return worksheet


@st.cache_resource(show_spinner=False)
def _temporary_wishes() -> list:
    """Wishes kept in memory when there is no Google Sheet (lost on restart)."""
    return []


def _worksheet_or_none():
    try:
        return _wishlist_worksheet()
    except Exception:
        return None


def is_permanent() -> bool:
    """True when wishes are saved to the Google Sheet."""
    return _worksheet_or_none() is not None


def clean_wishes(rows: list) -> pd.DataFrame:
    padded = [(list(r) + [""] * len(WISHLIST_COLUMNS))[: len(WISHLIST_COLUMNS)] for r in rows]
    frame = pd.DataFrame(padded, columns=WISHLIST_COLUMNS).fillna("").astype(str)
    return frame[frame["Wish ID"].str.strip() != ""].reset_index(drop=True)


def load_wishes() -> pd.DataFrame:
    worksheet = _worksheet_or_none()
    if worksheet is not None:
        return clean_wishes(worksheet.get_all_values()[1:])
    return clean_wishes(_temporary_wishes())


def save_wish(row: list) -> None:
    worksheet = _worksheet_or_none()
    if worksheet is not None:
        worksheet.append_row(row, value_input_option="RAW")
    else:
        _temporary_wishes().append(row)


def remove_wish(wish_id: str, student: str) -> None:
    """Deletes one of the student's own wishes (criterion 4). Others' wishes are never touched."""
    worksheet = _worksheet_or_none()
    if worksheet is not None:
        rows = worksheet.get_all_values()
        for number, row in enumerate(rows[1:], start=2):
            if row and row[0] == wish_id and len(row) > 1 and row[1].lower() == student.lower():
                worksheet.delete_rows(number)
                return
        return
    rows = _temporary_wishes()
    rows[:] = [r for r in rows if not (r[0] == wish_id and r[1].lower() == student.lower())]


def add_wish(title: str, author: str, student: str) -> str | None:
    """Checks and saves a wish. Returns an error message, or None when saved."""
    wishes = load_wishes()
    error = check_add(title, wishes, student)
    if error:
        return error
    save_wish(make_wish_row(next_wish_id(wishes), student, title, author))
    return None
