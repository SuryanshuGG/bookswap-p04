"""Listing a book (BS-25, story P04-US02) and reading every listed book.

Where books are kept:
- With the Google Sheet secrets set, books are read from and saved to the "Books"
  tab of that Google Sheet. That is permanent.
- Without them, books come from the Excel file in data/, and new listings are kept
  only until the app restarts. The listing page says so.
"""

import base64
import io
import json
from datetime import date

import pandas as pd
import streamlit as st

from bookswap.data import BOOK_COLUMNS, DATA_FILE, load_books as load_books_from_excel

CONDITIONS = ["Like New", "Good", "Fair"]
EXCHANGE_TYPES = ["Lend", "Swap", "Sell"]

# Error messages from Swasti's BS-24 design
ERRORS = {
    "title": "Title is required",
    "author": "Author is required",
    "course": "Choose a course",
    "genre": "Choose a genre",
    "photo": "Add a photo of the book",
    "condition": "Choose a condition",
    "exchange": "Choose an exchange type",
    "price": "Enter a price above ₹0 for Sell",
}


# ---------- Allowed values ----------

def load_choices(path=DATA_FILE) -> dict:
    """Course and genre options from the Lists sheet."""
    lists = pd.read_excel(path, sheet_name="Lists")
    return {
        "course": lists["Course"].dropna().astype(str).tolist(),
        "genre": lists["Genre"].dropna().astype(str).tolist(),
    }


# ---------- Checks (P04-US02, acceptance criteria 3 and 4) ----------

def check_listing(values: dict) -> dict:
    """Return {field: error message} for every required field that is missing or wrong."""
    errors = {}
    for field in ("title", "author"):
        if not str(values.get(field) or "").strip():
            errors[field] = ERRORS[field]
    for field in ("course", "genre", "photo", "condition", "exchange"):
        if not values.get(field):
            errors[field] = ERRORS[field]
    if values.get("exchange") == "Sell":
        price = values.get("price")
        if price is None or pd.isna(price) or float(price) <= 0:
            errors["price"] = ERRORS["price"]
    return errors


def next_book_id(books: pd.DataFrame) -> str:
    """BK-041 after BK-040, and so on."""
    numbers = books["Book ID"].astype(str).str.extract(r"(\d+)")[0].dropna().astype(int)
    return f"BK-{(numbers.max() if len(numbers) else 0) + 1:03d}"


def photo_to_data_uri(photo_bytes: bytes, max_chars: int = 45000) -> str:
    """Shrink the uploaded photo to a cover-sized JPEG small enough to fit in one
    Google Sheet cell, and return it as an image link the app can show."""
    from PIL import Image

    image = Image.open(io.BytesIO(photo_bytes))
    image = image.convert("RGB")
    image.thumbnail((300, 450))
    for quality in (75, 60, 45, 30):
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        uri = "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()
        if len(uri) <= max_chars:
            return uri
    image.thumbnail((160, 240))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=40)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()


def make_book_row(values: dict, owner: str, book_id: str, photo_uri: str, today: date | None = None) -> list:
    """One row for the Books sheet, in its column order. New books start as Available (AC5)."""
    sell = values["exchange"] == "Sell"
    return [
        book_id,
        values["title"].strip(),
        values["author"].strip(),
        values["course"],
        values["genre"],
        values["condition"],
        photo_uri,
        values["exchange"],
        int(values["price"]) if sell else "",
        owner,
        "Available",
        (today or date.today()).isoformat(),
    ]


# ---------- Reading and saving books ----------

def _secret(key: str):
    try:
        return st.secrets[key]
    except Exception:
        return None


@st.cache_resource(show_spinner=False)
def _books_worksheet():
    """The Books tab of the Google Sheet, or None if the secrets aren't set."""
    sheet_id, key_text = _secret("sheet_id"), _secret("service_account_json")
    if not sheet_id or not key_text:
        return None
    import gspread

    client = gspread.service_account_from_dict(json.loads(key_text))
    return client.open_by_key(sheet_id).worksheet("Books")


@st.cache_resource(show_spinner=False)
def _temporary_listings() -> list:
    """Listings kept in memory when there is no Google Sheet (lost on restart)."""
    return []


def _worksheet_or_none():
    try:
        return _books_worksheet()
    except Exception:
        return None


def is_permanent() -> bool:
    """True when new listings are saved to the Google Sheet."""
    return _worksheet_or_none() is not None


def clean_books(rows: pd.DataFrame) -> pd.DataFrame:
    """Same shape as the Excel books: every column present, empty rows dropped."""
    rows.columns = [str(c).strip() for c in rows.columns]
    for column in BOOK_COLUMNS:
        if column not in rows.columns:
            rows[column] = None
    rows = rows[BOOK_COLUMNS].replace("", None)
    rows = rows.dropna(subset=["Book ID", "Title"])
    rows["Price (Rs)"] = pd.to_numeric(rows["Price (Rs)"], errors="coerce")
    rows["Cover Image Link"] = rows["Cover Image Link"].fillna("").astype(str).str.strip()
    return rows.reset_index(drop=True)


def load_books() -> pd.DataFrame:
    """Every listed book: the Google Sheet if connected, else the Excel plus any test listings."""
    worksheet = _worksheet_or_none()
    if worksheet is not None:
        return clean_books(pd.DataFrame(worksheet.get_all_records()))
    books = load_books_from_excel()
    extra = _temporary_listings()
    if extra:
        books = pd.concat([books, clean_books(pd.DataFrame(extra, columns=BOOK_COLUMNS))], ignore_index=True)
    return books


def save_listing(row: list) -> None:
    worksheet = _worksheet_or_none()
    if worksheet is not None:
        worksheet.append_row(row, value_input_option="RAW")
    else:
        _temporary_listings().append(row)
