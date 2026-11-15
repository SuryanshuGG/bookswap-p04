"""Filter books by course and genre (BS-30, story P04-US04)."""

import pandas as pd

NO_FILTER_MATCH_MESSAGE = "No books found for these filters. Try another filter or clear them."


def filter_books(books: pd.DataFrame, course=None, genre=None, exchange=None) -> pd.DataFrame:
    """Books that match every filter that is set.

    - Course only: books tagged with that course (acceptance criterion 1).
    - Course and genre: books that match both (criterion 2).
    - Swap, Lend or Sell: books with that exchange type (criterion 6).
    - No filter set: every book (criterion 5).
    """
    shown = books
    if course:
        shown = shown[shown["Course"].astype(str) == str(course)]
    if genre:
        shown = shown[shown["Genre"].astype(str) == str(genre)]
    if exchange:
        shown = shown[shown["Exchange Type"].astype(str) == str(exchange)]
    return shown


def untagged_books(books: pd.DataFrame, choices: dict) -> pd.DataFrame:
    """Books whose course or genre is missing or not on the agreed list (criterion 3)."""
    bad_course = ~books["Course"].astype(str).isin(choices["course"])
    bad_genre = ~books["Genre"].astype(str).isin(choices["genre"])
    return books[bad_course | bad_genre]
