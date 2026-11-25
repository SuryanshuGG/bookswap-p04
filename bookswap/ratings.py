"""Rate my exchange partner, and report problems (BS-40, story P04-US09).

Acceptance criteria covered here:
1. After an exchange is completed, I can rate the other student from 1 to 5.
2. A profile shows the average rating.
3. Before the exchange is completed, rating isn't available.
4. I can't rate the same exchange twice.
5. A student with no ratings shows "No ratings yet".
6. Report a wrong listing or a student who breaks the guidelines, with a reason;
   the coordinator sees it in a Reports list.
(Criteria 7 to 9, email verification with Firebase, are set up separately by Suryanshu.)

Saved in "Ratings" and "Reports" tabs of the Google Sheet (made automatically).
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd

from bookswap import sheet_tabs

TAB = "Ratings"
COLUMNS = ["Rating ID", "Request ID", "Rater", "Rated", "Stars", "Date"]
REPORT_TAB = "Reports"
REPORT_COLUMNS = ["Report ID", "Reporter", "About Student", "About Book ID", "About Book", "Reason", "Details",
                  "Date", "Status"]
REASONS = ["Wrong or fake listing", "Broke the exchange guidelines", "Didn't turn up for the handover", "Something else"]

MESSAGES = {
    "not_done": "You can rate after both of you confirm the handover.",
    "already": "You've already rated this exchange.",
    "no_stars": "Choose 1 to 5 stars.",
    "not_party": "Only the two students in this exchange can rate it.",
    "rated": "Thanks! Your rating is saved.",
    "no_reason": "Choose a reason for the report.",
    "self": "You can't report yourself.",
    "reported": "Report sent. The literary club coordinator will look into it.",
    "no_ratings": "No ratings yet",
}


def today_ist() -> date:
    return datetime.now(ZoneInfo("Asia/Kolkata")).date()


def my_rating(ratings: pd.DataFrame, request_id: str, rater: str):
    if ratings.empty:
        return None
    rows = ratings[(ratings["Request ID"] == request_id) & (ratings["Rater"].str.lower() == str(rater).lower())]
    return rows.iloc[0].to_dict() if not rows.empty else None


def check_rating(exchange_done: bool, is_party: bool, already, stars) -> str | None:
    """Criteria 1, 3 and 4."""
    if not is_party:
        return MESSAGES["not_party"]
    if not exchange_done:
        return MESSAGES["not_done"]
    if already:
        return MESSAGES["already"]
    if stars in (None, "") or not 1 <= int(stars) <= 5:
        return MESSAGES["no_stars"]
    return None


def average(ratings: pd.DataFrame, student: str) -> tuple[float | None, int]:
    """(average, count) for a student; (None, 0) means "No ratings yet" (criteria 2 and 5)."""
    if ratings.empty:
        return None, 0
    rows = ratings[ratings["Rated"].str.lower() == str(student).lower()]
    stars = pd.to_numeric(rows["Stars"], errors="coerce").dropna()
    return (round(float(stars.mean()), 1), len(stars)) if len(stars) else (None, 0)


def check_report(reporter: str, about_student: str, reason: str | None) -> str | None:
    if not reason or reason not in REASONS:
        return MESSAGES["no_reason"]
    if str(reporter).lower() == str(about_student).lower():
        return MESSAGES["self"]
    return None


# ---------- Storage ----------

def load() -> pd.DataFrame:
    return sheet_tabs.load(TAB, COLUMNS)


def rate(request_id: str, rater: str, rated: str, stars, exchange_done: bool, is_party: bool) -> str | None:
    ratings = load()
    error = check_rating(exchange_done, is_party, my_rating(ratings, request_id, rater), stars)
    if error:
        return error
    sheet_tabs.append(TAB, COLUMNS, [sheet_tabs.next_id(ratings, "Rating ID", "RT"), request_id, rater, rated,
                                     str(int(stars)), today_ist().isoformat()])
    return None


def load_reports() -> pd.DataFrame:
    return sheet_tabs.load(REPORT_TAB, REPORT_COLUMNS)


def report(reporter: str, about_student: str, book_id: str, book_title: str, reason: str | None, details: str) -> str | None:
    error = check_report(reporter, about_student, reason)
    if error:
        return error
    reports = load_reports()
    sheet_tabs.append(REPORT_TAB, REPORT_COLUMNS, [sheet_tabs.next_id(reports, "Report ID", "RP"), reporter, about_student,
                                                   book_id, book_title, reason, str(details or "").strip()[:300],
                                                   today_ist().isoformat(), "Open"])
    return None


def close_report(report_id: str) -> None:
    sheet_tabs.update(REPORT_TAB, REPORT_COLUMNS, report_id, {"Status": "Closed"})
