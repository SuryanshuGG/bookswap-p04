"""Checks for BS-27 search rules, using the real 40 sample books."""

from bookswap.data import load_books
from bookswap.search import search_books

BOOKS = load_books()


def titles(text):
    return search_books(BOOKS, text)["Title"].tolist()


def test_part_of_a_title_finds_the_book():
    assert "Atomic Habits" in titles("habi")


def test_part_of_an_author_finds_their_books():
    assert "Marketing Management" in titles("kotl")


def test_capitals_do_not_matter():
    assert titles("KOTLER") == titles("kotler") == titles("Kotler")


def test_no_match_returns_nothing():
    assert titles("zzxqv") == []


def test_empty_search_shows_every_book():
    assert len(titles("")) == len(BOOKS)
    assert len(titles("   ")) == len(BOOKS)


def test_every_result_contains_the_text():
    for _, book in search_books(BOOKS, "market").iterrows():
        assert "market" in (book["Title"] + " " + book["Author"]).lower()
