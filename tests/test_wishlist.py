"""Tests for the wishlist rules (BS-42, story P04-US10)."""

from datetime import date

import pandas as pd

from bookswap import wishlist as w


def wishes(*rows):
    return w.clean_wishes([list(r) for r in rows])


def books(*rows):
    return pd.DataFrame(rows, columns=["Book ID", "Title", "Owner Name", "Status"])


def test_save_a_book_that_is_not_listed():  # criterion 1
    assert w.check_add("Principles of Corporate Finance", wishes(), "Krishna") is None
    row = w.make_wish_row("W-001", "Krishna", " Principles of Corporate Finance ", "Brealey", date(2026, 11, 23))
    assert row == ["W-001", "Krishna", "Principles of Corporate Finance", "Brealey", "2026-11-23"]


def test_title_is_required():
    assert w.check_add("   ", wishes(), "Krishna") == w.MESSAGES["no_title"]


def test_duplicate_is_refused_ignoring_case_and_punctuation():  # criterion 3
    saved = wishes(["W-001", "Krishna", "Atomic Habits", "", "2026-11-23"])
    assert w.check_add("atomic habits!", saved, "Krishna") == w.MESSAGES["duplicate"]
    assert w.check_add("Atomic Habits", saved, "Riya") is None  # someone else's wish doesn't count


def test_only_my_own_wishes_newest_first():  # criterion 5
    saved = wishes(["W-001", "Krishna", "A Book", "", "2026-11-20"], ["W-002", "Riya", "B Book", "", "2026-11-21"],
                   ["W-003", "krishna", "C Book", "", "2026-11-22"])
    assert list(w.my_wishes(saved, "Krishna")["Wish ID"]) == ["W-003", "W-001"]


def test_now_available_when_someone_else_lists_it():  # criterion 2
    listed = books(["BK-001", "Atomic Habits: Tiny Changes", "Riya", "Available"],
                   ["BK-002", "Deep Work", "Riya", "Reserved"],
                   ["BK-003", "Zero to One", "Krishna", "Available"])
    mine = w.with_matches(wishes(["W-001", "Krishna", "Atomic Habits", "", "x"], ["W-002", "Krishna", "Deep Work", "", "x"],
                                 ["W-003", "Krishna", "Zero to One", "", "x"]), listed, "Krishna")
    assert list(mine["Now Available"]) == [True, False, False]  # Reserved and own books don't count
    assert mine.iloc[0]["Match IDs"] == ["BK-001"]


def test_short_words_do_not_match_everything():
    assert not w.titles_match("The", "The Lean Startup")
    assert w.titles_match("Lean Startup", "The Lean Startup")
    assert not w.titles_match("Lean", "Clean Code")


def test_badge_counts_available_wishes():  # criterion 6
    listed = books(["BK-001", "Atomic Habits", "Riya", "Available"])
    saved = wishes(["W-001", "Krishna", "Atomic Habits", "", "x"], ["W-002", "Krishna", "Deep Work", "", "x"])
    assert w.badge_count(saved, listed, "Krishna") == 1
    assert w.badge_count(saved, listed, "Riya") == 0


def test_next_id():
    assert w.next_wish_id(wishes()) == "W-001"
    assert w.next_wish_id(wishes(["W-009", "K", "T", "", "x"])) == "W-010"


def test_remove_only_my_own_wish_in_test_mode():  # criterion 4
    store = w._temporary_wishes()
    store[:] = [["W-001", "Krishna", "Atomic Habits", "", "x"], ["W-002", "Riya", "Atomic Habits", "", "x"]]
    w.remove_wish("W-002", "Krishna")  # not mine: untouched
    w.remove_wish("W-001", "Krishna")
    assert [r[0] for r in store] == ["W-002"]
    store.clear()
