"""Who can sign in, and sign-up for new students (BS-55).

Where users are kept:
- When Streamlit has the Google Sheet secrets (sheet_id and service_account_json),
  users are read from and saved to the "Users" tab of that Google Sheet. That is permanent.
- Without those secrets, users come from the Excel file in data/, and anyone who signs up
  is kept only until the app restarts. The sign-up page says so.
"""

import json
import re

import pandas as pd
import streamlit as st

from bookswap.data import load_users as load_users_from_excel

USER_COLUMNS = ["Name", "Role", "College Email"]
COLLEGE_DOMAIN = "xime.org"
_EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


# ---------- Checks for the sign-up form ----------

def check_sign_up(name: str, email: str, users: pd.DataFrame) -> str | None:
    """Return an error message, or None if the sign-up can go ahead."""
    name, email = name.strip(), email.strip().lower()
    if not name:
        return "Please enter your full name."
    if not email:
        return "Please enter your college email."
    if not _EMAIL_PATTERN.match(email):
        return "Please enter a valid email, like name@xime.org."
    if not email.endswith("@" + COLLEGE_DOMAIN):
        return f"Please use your college email ending in @{COLLEGE_DOMAIN}."
    if name.lower() in users["Name"].str.strip().str.lower().tolist():
        return "Someone with this name already has an account. Please sign in instead."
    if email in users["College Email"].str.strip().str.lower().tolist():
        return "This email already has an account. Please sign in instead."
    return None


def clean_users(rows: pd.DataFrame) -> pd.DataFrame:
    """Keep only real user rows with the three columns the app uses."""
    for column in USER_COLUMNS:
        if column not in rows.columns:
            rows[column] = ""
    rows = rows[USER_COLUMNS].fillna("").astype(str)
    rows = rows[(rows["Name"].str.strip() != "") & (rows["Role"].str.strip() != "")]
    return rows.reset_index(drop=True)


# ---------- Google Sheet connection ----------

def _secret(key: str):
    try:
        return st.secrets[key]
    except Exception:
        return None


@st.cache_resource(show_spinner=False)
def _users_worksheet():
    """The Users tab of the Google Sheet, or None if the secrets aren't set."""
    sheet_id, key_text = _secret("sheet_id"), _secret("service_account_json")
    if not sheet_id or not key_text:
        return None
    import gspread

    client = gspread.service_account_from_dict(json.loads(key_text))
    return client.open_by_key(sheet_id).worksheet("Users")


@st.cache_resource(show_spinner=False)
def _temporary_sign_ups() -> list:
    """Sign-ups kept in memory when there is no Google Sheet (lost on restart)."""
    return []


def is_permanent() -> bool:
    """True when sign-ups are saved to the Google Sheet."""
    try:
        return _users_worksheet() is not None
    except Exception:
        return False


# ---------- Reading and adding users ----------

def load_users() -> pd.DataFrame:
    """Everyone who can sign in."""
    worksheet = None
    try:
        worksheet = _users_worksheet()
    except Exception:
        worksheet = None
    if worksheet is not None:
        return clean_users(pd.DataFrame(worksheet.get_all_records()))
    users = clean_users(load_users_from_excel())
    extra = pd.DataFrame(_temporary_sign_ups(), columns=USER_COLUMNS)
    return pd.concat([users, extra], ignore_index=True)


def add_user(name: str, email: str) -> None:
    """Save a new student: to the Google Sheet if connected, otherwise in memory."""
    row = [name.strip(), "Student", email.strip().lower()]
    worksheet = _users_worksheet() if is_permanent() else None
    if worksheet is not None:
        worksheet.append_row(row, value_input_option="RAW")
    else:
        _temporary_sign_ups().append(row)
