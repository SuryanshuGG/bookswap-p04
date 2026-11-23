"""Reading circle announcements (BS-49, story P04-US13).

Rules (acceptance criteria):
1. A posted announcement shows on the home screen.
2. Once its event date has passed, it is hidden.
3. Title, date, time and venue are all required.
4. Several live announcements are shown soonest first.
5. Only the literary club coordinator can post or edit them.
Saved in an "Announcements" tab of the Google Sheet (made automatically).
"""

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

import pandas as pd

from bookswap import sheet_tabs

TAB = "Announcements"
COLUMNS = ["Announcement ID", "Title", "Event Date", "Event Time", "Venue", "Details", "Posted By", "Posted On"]
COORDINATOR_ROLES = ("coordinator", "product owner")  # Chandana plays the literary club coordinator

MESSAGES = {
    "missing": "Please fill in the title, date, time and venue.",
    "past": "Choose today or a future date for the event.",
    "not_coordinator": "Only the literary club coordinator can post announcements.",
    "posted": "Announcement posted. Students see it on the home screen.",
    "deleted": "Announcement removed.",
}


def today_ist() -> date:
    """Campus date. The app's server runs on UTC."""
    return datetime.now(ZoneInfo("Asia/Kolkata")).date()


def is_coordinator(name: str, users: pd.DataFrame) -> bool:
    """Criterion 5: the user's Role on the Users list says Coordinator (or Product Owner)."""
    role = users.loc[users["Name"].str.lower() == str(name).lower(), "Role"]
    return not role.empty and str(role.iloc[0]).strip().lower() in COORDINATOR_ROLES


def check_post(title: str, event_date: date | None, event_time: time | None, venue: str,
               poster_is_coordinator: bool, today: date | None = None) -> str | None:
    """Error message, or None if it can be posted (criteria 3 and 5)."""
    if not poster_is_coordinator:
        return MESSAGES["not_coordinator"]
    if not str(title).strip() or event_date is None or event_time is None or not str(venue).strip():
        return MESSAGES["missing"]
    if event_date < (today or today_ist()):
        return MESSAGES["past"]
    return None


def make_row(announcement_id: str, title: str, event_date: date, event_time: time, venue: str, details: str,
             poster: str, today: date | None = None) -> list:
    return [announcement_id, title.strip(), event_date.isoformat(), event_time.strftime("%H:%M"), venue.strip(),
            details.strip(), poster, (today or today_ist()).isoformat()]


def live(announcements: pd.DataFrame, today: date | None = None) -> pd.DataFrame:
    """Announcements whose event is today or later, soonest first (criteria 2 and 4)."""
    if announcements.empty:
        return announcements
    today_text = (today or today_ist()).isoformat()
    upcoming = announcements[announcements["Event Date"] >= today_text]
    return upcoming.sort_values(["Event Date", "Event Time"]).reset_index(drop=True)




# ---------- Storage ----------

def load() -> pd.DataFrame:
    frame = sheet_tabs.load(TAB, COLUMNS)
    return frame[frame["Title"] != "(removed)"].reset_index(drop=True) if not frame.empty else frame


def post(title, event_date, event_time, venue, details, poster: str, users: pd.DataFrame) -> str | None:
    error = check_post(title, event_date, event_time, venue, is_coordinator(poster, users))
    if error:
        return error
    all_rows = sheet_tabs.load(TAB, COLUMNS)
    sheet_tabs.append(TAB, COLUMNS, make_row(sheet_tabs.next_id(all_rows, "Announcement ID", "AN"),
                                             title, event_date, event_time, venue, details or "", poster))
    return None


def remove(announcement_id: str, user: str, users: pd.DataFrame) -> str | None:
    """Coordinator only. The row is kept in the Sheet but marked removed."""
    if not is_coordinator(user, users):
        return MESSAGES["not_coordinator"]
    sheet_tabs.update(TAB, COLUMNS, announcement_id, {"Title": "(removed)"})
    return None


def is_permanent() -> bool:
    return sheet_tabs.is_permanent(TAB, COLUMNS)
