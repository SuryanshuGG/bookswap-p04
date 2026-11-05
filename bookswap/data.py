"""Reads the BookSwap data (books and users) from the Excel file in data/.

The app reads the file every time it loads, so a new row added to the Books
sheet shows up without any change to the code (US01, acceptance criterion 5).
"""

from pathlib import Path

import pandas as pd

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "BookSwap_40_Books.xlsx"

# Column names as they appear in the Books sheet.
BOOK_COLUMNS = [
    "Book ID",
    "Title",
    "Author",
    "Course",
    "Genre",
    "Condition",
    "Cover Image Link",
    "Exchange Type",
    "Price (Rs)",
    "Owner Name",
    "Status",
    "Date Listed",
]


def load_books(path: Path = DATA_FILE) -> pd.DataFrame:
    """Return every book in the Books sheet, skipping empty rows."""
    books = pd.read_excel(path, sheet_name="Books")
    books.columns = [str(c).strip() for c in books.columns]
    books = books.dropna(subset=["Book ID", "Title"])
    for column in BOOK_COLUMNS:
        if column not in books.columns:
            books[column] = None
    books["Cover Image Link"] = books["Cover Image Link"].fillna("").astype(str).str.strip()
    return books[BOOK_COLUMNS].reset_index(drop=True)


def load_users(path: Path = DATA_FILE) -> pd.DataFrame:
    """Return the people who can sign in (the Users sheet)."""
    users = pd.read_excel(path, sheet_name="Users")
    users.columns = [str(c).strip() for c in users.columns]
    users = users.dropna(subset=["Name"])
    users = users[users["Role"].notna()]
    users["College Email"] = users["College Email"].fillna("").astype(str).str.strip()
    return users[["Name", "Role", "College Email"]].reset_index(drop=True)
