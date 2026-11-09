"""Search books by title or author (BS-27, story P04-US03)."""

import pandas as pd

NO_MATCH_MESSAGE = "No books found. Add it to your wishlist and we'll tell you when someone lists it."


def search_books(books: pd.DataFrame, text: str) -> pd.DataFrame:
    """Books whose title or author contains the text.

    - Part of a word is enough: "kotl" finds Kotler (acceptance criteria 1 and 3).
    - Capitals don't matter: "KOTLER" and "kotler" give the same result (criterion 4).
    - An empty search box returns every book (criterion 5).
    """
    query = (text or "").strip().lower()
    if not query:
        return books
    in_title = books["Title"].astype(str).str.lower().str.contains(query, regex=False)
    in_author = books["Author"].astype(str).str.lower().str.contains(query, regex=False)
    return books[in_title | in_author]
