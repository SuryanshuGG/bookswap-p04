"""Short peer reviews of a book (BS-53, story P04-US15).

Acceptance criteria:
1. A book's reviews are listed with their ratings.
2. A review is at most 100 words.
3. A rating from 1 to 5 is required.
4. Reviewing the same book again edits my review instead of adding a second one.
5. A book with no reviews shows "No reviews yet".

Reviews belong to the title (normalised), so every copy of a book shares them.
Saved in a "Reviews" tab of the Google Sheet (made automatically).
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd

from bookswap import sheet_tabs
from bookswap.wishlist import normalise

TAB = "Reviews"
COLUMNS = ["Review ID", "Title Key", "Book Title", "Student", "Stars", "Review", "Date"]
MAX_WORDS = 100

MESSAGES = {
    "no_stars": "Choose a rating from 1 to 5 stars.",
    "too_long": f"Keep your review to {MAX_WORDS} words or fewer.",
    "empty": "Write a few words about the book.",
    "saved": "Thanks! Your review is posted.",
    "updated": "Your review is updated.",
    "none": "No reviews yet",
}


def today_ist() -> date:
    return datetime.now(ZoneInfo("Asia/Kolkata")).date()


def word_count(text: str) -> int:
    return len(str(text or "").split())


def check_review(stars, text: str) -> str | None:
    """Criteria 2 and 3."""
    if stars in (None, "") or not 1 <= int(stars) <= 5:
        return MESSAGES["no_stars"]
    if word_count(text) == 0:
        return MESSAGES["empty"]
    if word_count(text) > MAX_WORDS:
        return MESSAGES["too_long"]
    return None


def for_title(reviews: pd.DataFrame, title: str) -> pd.DataFrame:
    """Reviews for this title, newest first (criterion 1)."""
    if reviews.empty:
        return reviews
    rows = reviews[reviews["Title Key"] == normalise(title)]
    return rows.sort_values("Date", ascending=False).reset_index(drop=True)


def summary(rows: pd.DataFrame) -> tuple[float | None, int]:
    """(average stars, count); (None, 0) when there are none (criterion 5)."""
    if rows.empty:
        return None, 0
    stars = pd.to_numeric(rows["Stars"], errors="coerce").dropna()
    return (round(float(stars.mean()), 1) if len(stars) else None), len(rows)


def mine(reviews: pd.DataFrame, title: str, student: str):
    """My existing review of this title as a dict, or None (criterion 4)."""
    rows = for_title(reviews, title)
    if rows.empty:
        return None
    match = rows[rows["Student"].str.lower() == str(student).lower()]
    return match.iloc[0].to_dict() if not match.empty else None


# ---------- Storage ----------

def load() -> pd.DataFrame:
    return sheet_tabs.load(TAB, COLUMNS)


def save(title: str, student: str, stars, text: str) -> tuple[str | None, str]:
    """Adds or edits my review. Returns (error, message)."""
    error = check_review(stars, text)
    if error:
        return error, ""
    reviews = load()
    existing = mine(reviews, title, student)
    values = {"Stars": str(int(stars)), "Review": " ".join(str(text).split()), "Date": today_ist().isoformat()}
    if existing:
        sheet_tabs.update(TAB, COLUMNS, existing["Review ID"], values)
        return None, MESSAGES["updated"]
    sheet_tabs.append(TAB, COLUMNS, [sheet_tabs.next_id(reviews, "Review ID", "RV"), normalise(title), title.strip(),
                                     student, values["Stars"], values["Review"], values["Date"]])
    return None, MESSAGES["saved"]


def is_permanent() -> bool:
    return sheet_tabs.is_permanent(TAB, COLUMNS)
