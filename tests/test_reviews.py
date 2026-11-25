"""Tests for peer reviews (BS-53, story P04-US15)."""

from bookswap import reviews as r
from bookswap import sheet_tabs


def test_rating_required_and_100_word_limit():  # criteria 2 and 3
    assert r.check_review(None, "Great book") == r.MESSAGES["no_stars"]
    assert r.check_review(0, "Great book") == r.MESSAGES["no_stars"]
    assert r.check_review(4, "") == r.MESSAGES["empty"]
    assert r.check_review(4, "word " * 101) == r.MESSAGES["too_long"]
    assert r.check_review(4, "word " * 100) is None


def test_no_reviews_yet():  # criterion 5
    assert r.summary(r.for_title(sheet_tabs.to_frame([], r.COLUMNS), "Atomic Habits")) == (None, 0)


def test_one_review_per_student_is_edited_and_listed_with_ratings():  # criteria 1 and 4
    store = sheet_tabs._memory(r.TAB); store.clear()
    assert r.save("Atomic Habits", "Krishna", 4, "Practical and short.") == (None, r.MESSAGES["saved"])
    assert r.save("atomic habits", "Krishna", 5, "Even better second time.") == (None, r.MESSAGES["updated"])
    assert r.save("Atomic Habits", "Riya", 3, "Good, a bit repetitive.") == (None, r.MESSAGES["saved"])
    rows = r.for_title(r.load(), "Atomic Habits")
    assert len(rows) == 2 and set(rows["Student"]) == {"Krishna", "Riya"}
    assert r.mine(r.load(), "Atomic Habits", "krishna")["Stars"] == "5"
    assert r.summary(rows) == (4.0, 2)
    store.clear()
