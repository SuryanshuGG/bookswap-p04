"""Tests for the guidelines and how-to content (story P04-US11)."""

from bookswap import help as h


def test_how_to_has_five_steps_or_fewer():  # criterion 2
    assert 1 <= len(h.HOW_TO) <= 5
    text = " ".join(t for _, t in h.HOW_TO)
    assert "List a book" in text and "Request this book" in text


def test_guidelines_cover_pricing_condition_and_safe_meeting():  # criterion 1
    titles = [t for t, _ in h.GUIDELINES]
    assert {"Fair pricing", "Book condition", "Safe meeting"} <= set(titles)


def test_safe_meeting_names_the_approved_points():  # criterion 3
    assert len(h.handover_point_names()) >= 3
    safe = dict(h.GUIDELINES)["Safe meeting"]
    assert any("approved handover point" in rule for rule in safe)
