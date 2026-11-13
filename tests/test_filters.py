"""Checks for the course and genre filters (BS-30, story P04-US04)."""

from bookswap.data import load_books
from bookswap.filters import filter_books, untagged_books
from bookswap.listings import load_choices
from bookswap.search import search_books

BOOKS = load_books()
CHOICES = load_choices()


def test_course_only_shows_books_tagged_for_it():
    shown = filter_books(BOOKS, course="Finance")
    assert len(shown) > 0
    assert (shown["Course"] == "Finance").all()


def test_course_and_genre_must_both_match():
    shown = filter_books(BOOKS, course="General Interest", genre="Psychology")
    assert len(shown) >= 1
    assert (shown["Course"] == "General Interest").all()
    assert (shown["Genre"] == "Psychology").all()


def test_every_sample_book_has_an_agreed_course_and_genre():
    assert untagged_books(BOOKS, CHOICES).empty


def test_combination_with_no_books_is_empty():
    assert filter_books(BOOKS, course="Finance", genre="Fiction").empty


def test_no_filter_returns_full_list():
    assert len(filter_books(BOOKS)) == len(BOOKS)
    assert len(filter_books(BOOKS, course=None, genre=None)) == 40


def test_filters_work_with_search():
    shown = filter_books(search_books(BOOKS, "the"), course="Marketing")
    assert (shown["Course"] == "Marketing").all()
    assert shown["Title"].str.lower().str.contains("the").any() or shown["Author"].str.lower().str.contains("the").any()
