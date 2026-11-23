"""Campus handover after a request is accepted (BS-39, story P04-US08).

Acceptance criteria:
1. Only approved campus handover points can be chosen.
2. When both students confirm the handover, the book becomes Exchanged.
3. Only a future date and time is accepted.
4. While only one student has confirmed, the book stays Reserved.
5. Both students see the agreed point, date and time.
6. For a Sell book, the owner marks it Paid and the request shows Paid with the amount.
7. Two days before a lent book is due, the borrower sees a reminder.
8. The owner marks a lent book Returned and it becomes Available; after the date it shows Overdue.
9. The two students can send each other short messages to agree the handover.

Saved in "Handovers" and "Messages" tabs of the Google Sheet (made automatically).
"""

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

import pandas as pd

from bookswap import sheet_tabs
from bookswap.help import HANDOVER_POINTS, handover_point_names

TAB = "Handovers"
COLUMNS = ["Request ID", "Point", "Date", "Time", "Proposed By", "Owner Done", "Requester Done",
           "Paid", "Paid Amount", "Returned", "Updated"]
MESSAGE_TAB = "Messages"
MESSAGE_COLUMNS = ["Message ID", "Request ID", "Sender", "Text", "Sent At"]
OPEN_HOUR, CLOSE_HOUR = 8, 20  # handovers between 8:00 am and 8:00 pm (exchange guidelines)
MAX_MESSAGE = 200
REMIND_DAYS = 2

MESSAGES = {
    "bad_point": "Choose one of the approved campus handover points.",
    "missing": "Choose a handover point, date and time.",
    "past": "Choose a date and time in the future.",
    "hours": "Choose a time between 8:00 am and 8:00 pm.",
    "not_party": "Only the two students in this exchange can do this.",
    "not_accepted": "This request isn't accepted yet.",
    "not_scheduled": "Agree a handover point and time first.",
    "already_done": "You've already confirmed this handover.",
    "not_exchanged": "Do this after both of you confirm the handover.",
    "owner_only": "Only the book's owner can do this.",
    "not_sell": "Only books for sale are marked Paid.",
    "not_lend": "Only lent books are marked Returned.",
    "already": "This is already done.",
    "empty_message": "Type a message first.",
    "long_message": f"Keep messages to {MAX_MESSAGE} characters or fewer.",
}


# ---------- Rules ----------

def now_ist() -> datetime:
    """Campus time. The app's server runs on UTC, so 'future' is checked in India time."""
    return datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)


def role_of(user: str, request: pd.Series, book: pd.Series) -> str | None:
    """'owner', 'requester', or None for anyone else."""
    if str(book["Owner Name"]).lower() == str(user).lower():
        return "owner"
    if str(request["Requester Name"]).lower() == str(user).lower():
        return "requester"
    return None


def check_schedule(point: str | None, day: date | None, at: time | None, now: datetime | None = None) -> str | None:
    """Error message, or None if the plan can be saved (criteria 1 and 3)."""
    if not point or day is None or at is None:
        return MESSAGES["missing"]
    if point not in handover_point_names():
        return MESSAGES["bad_point"]
    if not (OPEN_HOUR <= at.hour < CLOSE_HOUR or (at.hour == CLOSE_HOUR and at.minute == 0)):
        return MESSAGES["hours"]
    if datetime.combine(day, at) <= (now or now_ist()):
        return MESSAGES["past"]
    return None


def is_scheduled(handover) -> bool:
    return handover is not None and bool(str(handover.get("Point", "")).strip())


def plan_confirm(handover, request: pd.Series, book: pd.Series, user: str):
    """Returns (error, handover_changes, book_changes, other_book_changes) for 'Handover done'.

    Criteria 2 and 4: the book becomes Exchanged only when both have confirmed.
    For a swap, the offered book changes hands too, so it is marked Exchanged as well.
    """
    role = role_of(user, request, book)
    if role is None:
        return MESSAGES["not_party"], {}, {}, {}
    if request["Status"] != "Accepted":
        return MESSAGES["not_accepted"], {}, {}, {}
    if not is_scheduled(handover):
        return MESSAGES["not_scheduled"], {}, {}, {}
    mine, theirs = ("Owner Done", "Requester Done") if role == "owner" else ("Requester Done", "Owner Done")
    if handover.get(mine) == "yes":
        return MESSAGES["already_done"], {}, {}, {}
    changes = {mine: "yes"}
    if handover.get(theirs) == "yes":
        return None, changes, {"Status": "Exchanged"}, ({"Status": "Exchanged"} if request.get("Offered Book ID") else {})
    return None, changes, {}, {}


def both_done(handover) -> bool:
    return handover is not None and handover.get("Owner Done") == "yes" and handover.get("Requester Done") == "yes"


def plan_paid(handover, request: pd.Series, book: pd.Series, user: str):
    """Criterion 6: the owner marks a Sell book Paid with its amount. Returns (error, changes)."""
    if role_of(user, request, book) != "owner":
        return MESSAGES["owner_only"], {}
    if book["Exchange Type"] != "Sell":
        return MESSAGES["not_sell"], {}
    if not both_done(handover):
        return MESSAGES["not_exchanged"], {}
    if handover.get("Paid") == "yes":
        return MESSAGES["already"], {}
    price = book["Price (Rs)"]
    amount = str(int(float(price))) if str(price).strip() not in ("", "nan") else ""
    return None, {"Paid": "yes", "Paid Amount": amount}


def plan_returned(handover, request: pd.Series, book: pd.Series, user: str):
    """Criterion 8: the owner marks a lent book Returned; it becomes Available.
    Returns (error, handover_changes, book_changes)."""
    if role_of(user, request, book) != "owner":
        return MESSAGES["owner_only"], {}, {}
    if book["Exchange Type"] != "Lend":
        return MESSAGES["not_lend"], {}, {}
    if not both_done(handover):
        return MESSAGES["not_exchanged"], {}, {}
    if handover.get("Returned") == "yes":
        return MESSAGES["already"], {}, {}
    return None, {"Returned": "yes"}, {"Status": "Available"}


def lend_status(request: pd.Series, handover, today: date | None = None) -> str:
    """For a lent book: '', 'On loan', 'Due soon', 'Overdue' or 'Returned' (criteria 7 and 8)."""
    if not both_done(handover) or not str(request.get("Return Date", "")).strip():
        return ""
    if handover.get("Returned") == "yes":
        return "Returned"
    days_left = (date.fromisoformat(str(request["Return Date"])) - (today or now_ist().date())).days
    if days_left < 0:
        return "Overdue"
    if days_left <= REMIND_DAYS:
        return "Due soon"
    return "On loan"


def reminders(requests: pd.DataFrame, books: pd.DataFrame, handovers: pd.DataFrame, user: str,
              today: date | None = None) -> list[str]:
    """Reminders for the borrower when they open BookSwap (criteria 7 and 8)."""
    notes = []
    mine = requests[(requests["Requester Name"].str.lower() == str(user).lower()) & (requests["Status"] == "Accepted")]
    for _, request in mine.iterrows():
        book = books[books["Book ID"] == request["Book ID"]]
        if book.empty or book.iloc[0]["Exchange Type"] != "Lend":
            continue
        status = lend_status(request, find(handovers, request["Request ID"]), today)
        due = date.fromisoformat(str(request["Return Date"])).strftime("%-d %b") if status else ""
        if status == "Due soon":
            notes.append(f"Reminder: return {book.iloc[0]['Title']} to {book.iloc[0]['Owner Name']} by {due}.")
        elif status == "Overdue":
            notes.append(f"Overdue: {book.iloc[0]['Title']} was due back to {book.iloc[0]['Owner Name']} on {due}.")
    return notes


def check_message(text: str) -> str | None:
    """Criterion 9: short messages only."""
    text = str(text or "").strip()
    if not text:
        return MESSAGES["empty_message"]
    if len(text) > MAX_MESSAGE:
        return MESSAGES["long_message"]
    return None


def find(handovers: pd.DataFrame, request_id: str):
    """The handover row (as a dict) for a request, or None."""
    if handovers.empty:
        return None
    row = handovers[handovers["Request ID"] == request_id]
    return row.iloc[0].to_dict() if not row.empty else None


def point_where(name: str) -> str:
    return dict(HANDOVER_POINTS).get(name, "")


# ---------- Storage ----------

def load() -> pd.DataFrame:
    return sheet_tabs.load(TAB, COLUMNS)


def load_messages(request_id: str) -> pd.DataFrame:
    rows = sheet_tabs.load(MESSAGE_TAB, MESSAGE_COLUMNS)
    return rows[rows["Request ID"] == request_id].reset_index(drop=True) if not rows.empty else rows


def save_schedule(request_id: str, point: str, day: date, at: time, user: str) -> None:
    """Saves or changes the plan. A changed plan clears earlier confirmations."""
    values = {"Point": point, "Date": day.isoformat(), "Time": at.strftime("%H:%M"), "Proposed By": user,
              "Owner Done": "", "Requester Done": "", "Updated": now_ist().isoformat(timespec="minutes")}
    if find(load(), request_id) is None:
        sheet_tabs.append(TAB, COLUMNS, [request_id] + [values.get(c, "") for c in COLUMNS[1:]])
    else:
        sheet_tabs.update(TAB, COLUMNS, request_id, values)


def save_changes(request_id: str, changes: dict) -> None:
    sheet_tabs.update(TAB, COLUMNS, request_id, {**changes, "Updated": now_ist().isoformat(timespec="minutes")})


def send_message(request_id: str, sender: str, text: str) -> None:
    rows = sheet_tabs.load(MESSAGE_TAB, MESSAGE_COLUMNS)
    sheet_tabs.append(MESSAGE_TAB, MESSAGE_COLUMNS, [sheet_tabs.next_id(rows, "Message ID", "MS"), request_id, sender,
                                                     str(text).strip(), now_ist().isoformat(timespec="minutes")])
