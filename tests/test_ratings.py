"""Tests for rating an exchange partner and reporting (BS-40, story P04-US09)."""

from bookswap import ratings as r
from bookswap import sheet_tabs


def test_rate_only_after_exchange_once_with_stars():  # criteria 1, 3 and 4
    assert r.check_rating(False, True, None, 5) == r.MESSAGES["not_done"]
    assert r.check_rating(True, False, None, 5) == r.MESSAGES["not_party"]
    assert r.check_rating(True, True, {"Stars": "4"}, 5) == r.MESSAGES["already"]
    assert r.check_rating(True, True, None, None) == r.MESSAGES["no_stars"]
    assert r.check_rating(True, True, None, 5) is None


def test_average_and_no_ratings_yet():  # criteria 2 and 5
    store = sheet_tabs._memory(r.TAB); store.clear()
    assert r.average(r.load(), "Riya") == (None, 0)
    assert r.rate("RQ-001", "Krishna", "Riya", 5, True, True) is None
    assert r.rate("RQ-001", "Krishna", "Riya", 3, True, True) == r.MESSAGES["already"]
    assert r.rate("RQ-002", "Nandan", "Riya", 4, True, True) is None
    assert r.average(r.load(), "riya") == (4.5, 2)
    store.clear()


def test_report_needs_reason_and_reaches_the_list():  # criterion 6
    store = sheet_tabs._memory(r.REPORT_TAB); store.clear()
    assert r.report("Krishna", "Riya", "BK-016", "Data Science", None, "") == r.MESSAGES["no_reason"]
    assert r.report("Riya", "Riya", "BK-016", "Data Science", r.REASONS[0], "") == r.MESSAGES["self"]
    assert r.report("Krishna", "Riya", "BK-016", "Data Science", r.REASONS[1], "Asked to pay first") is None
    reports = r.load_reports()
    assert reports.iloc[0]["Status"] == "Open" and reports.iloc[0]["Reason"] == r.REASONS[1]
    r.close_report(reports.iloc[0]["Report ID"])
    assert r.load_reports().iloc[0]["Status"] == "Closed"
    store.clear()
