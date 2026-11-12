"""Checks for BS-25 listing rules (P04-US02 acceptance criteria)."""

import io
from datetime import date

from PIL import Image

from bookswap.data import BOOK_COLUMNS, load_books
from bookswap.listings import (
    ERRORS, check_listing, clean_books, load_choices, make_book_row, next_book_id, photo_to_data_uri,
)

GOOD = {
    "title": "Test Book", "author": "Test Author", "course": "Finance", "genre": "Finance",
    "photo": b"x", "condition": "Good", "exchange": "Swap", "price": None,
}


def test_complete_swap_listing_has_no_errors_and_needs_no_price():
    assert check_listing(GOOD) == {}
    assert check_listing({**GOOD, "exchange": "Lend"}) == {}


def test_each_required_field_gives_its_own_error():
    for field in ("title", "author", "course", "genre", "photo", "condition", "exchange"):
        errors = check_listing({**GOOD, field: "" if field in ("title", "author") else None})
        assert errors == {field: ERRORS[field]}, field


def test_blank_title_with_spaces_is_still_blank():
    assert check_listing({**GOOD, "title": "   "}) == {"title": "Title is required"}


def test_sell_needs_a_price_above_zero():
    assert check_listing({**GOOD, "exchange": "Sell", "price": None}) == {"price": ERRORS["price"]}
    assert check_listing({**GOOD, "exchange": "Sell", "price": 0}) == {"price": ERRORS["price"]}
    assert check_listing({**GOOD, "exchange": "Sell", "price": 250}) == {}


def test_new_book_gets_the_next_id():
    assert next_book_id(load_books()) == "BK-041"


def test_saved_row_is_available_under_the_owner_with_price_only_for_sell():
    row = dict(zip(BOOK_COLUMNS, make_book_row({**GOOD, "exchange": "Sell", "price": 250}, "Krishna", "BK-041", "data:x", date(2026, 11, 9))))
    assert row["Owner Name"] == "Krishna" and row["Status"] == "Available"
    assert row["Price (Rs)"] == 250 and row["Date Listed"] == "2026-11-09"
    swap = dict(zip(BOOK_COLUMNS, make_book_row(GOOD, "Krishna", "BK-042", "data:x")))
    assert swap["Price (Rs)"] == ""


def test_saved_row_reads_back_like_the_excel_books():
    rows = [make_book_row({**GOOD, "exchange": "Sell", "price": 250}, "Krishna", "BK-041", "data:x")]
    import pandas as pd
    books = clean_books(pd.DataFrame(rows, columns=BOOK_COLUMNS))
    assert books.loc[0, "Price (Rs)"] == 250 and books.loc[0, "Title"] == "Test Book"


def test_large_photo_is_shrunk_to_fit_one_sheet_cell():
    buffer = io.BytesIO()
    Image.effect_noise((2400, 3200), 80).convert("RGB").save(buffer, format="PNG")
    uri = photo_to_data_uri(buffer.getvalue())
    assert uri.startswith("data:image/jpeg;base64,") and len(uri) <= 45000


def test_course_and_genre_choices_come_from_the_lists_sheet():
    choices = load_choices()
    assert "Marketing" in choices["course"] and "Fiction" in choices["genre"]
