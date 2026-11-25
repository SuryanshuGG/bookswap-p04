"""Verified sign-in with Firebase Authentication (BS-40, story P04-US09 criteria 7 to 9).

7. Sign up with an @xime.org email and a password: a verification email is sent,
   and the student can't sign in until they open its link.
8. Once verified, sign in with email and password; a wrong password or an
   unverified email is refused with a clear message.
9. If the name (and roll number, where recorded) isn't on the approved Users list,
   sign-up is refused and the student is asked to contact the coordinator.

Switched on by one Streamlit secret, firebase_api_key (Firebase project settings,
Web API key), with Email/Password sign-in enabled in the Firebase console.
Without it the app keeps the Sprint 1 name-and-email sign-in.
Uses Firebase's REST API, so no extra Python package is needed.
"""

import json
import re
import urllib.error
import urllib.request

import pandas as pd
import streamlit as st

COLLEGE_DOMAIN = "xime.org"
MIN_PASSWORD = 6  # Firebase's own minimum
_ENDPOINT = "https://identitytoolkit.googleapis.com/v1/accounts:{action}?key={key}"
_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

MESSAGES = {
    "name": "Please enter your full name.",
    "roll": "Please enter your roll number.",
    "email": f"Please use your college email ending in @{COLLEGE_DOMAIN}.",
    "password": f"Use a password of at least {MIN_PASSWORD} characters.",
    "not_approved": "Your name and roll number aren't on the approved list. Please contact the literary club coordinator.",
    "email_taken": "This email already belongs to another student. Please sign in instead.",
    "check_inbox": "Account created. We sent a verification link to {email}. Open it, then sign in.",
    "unverified": "Verify your email first. Open the link we sent to {email}, then sign in again.",
    "resent": "We sent a new verification link to {email}.",
    "not_on_list": "This email isn't on the Users list. Please contact the literary club coordinator.",
}

FIREBASE_ERRORS = {
    "EMAIL_EXISTS": "An account already exists for this email. Please sign in instead.",
    "WEAK_PASSWORD": f"Use a password of at least {MIN_PASSWORD} characters.",
    "INVALID_LOGIN_CREDENTIALS": "Wrong email or password.",
    "INVALID_PASSWORD": "Wrong email or password.",
    "EMAIL_NOT_FOUND": "Wrong email or password.",
    "INVALID_EMAIL": f"Please use your college email ending in @{COLLEGE_DOMAIN}.",
    "TOO_MANY_ATTEMPTS_TRY_LATER": "Too many tries. Please wait a few minutes and try again.",
    "USER_DISABLED": "This account is turned off. Please contact the literary club coordinator.",
    "OPERATION_NOT_ALLOWED": "Email sign-in isn't switched on in Firebase yet. Please tell the team.",
}


def _secret(key: str):
    try:
        return st.secrets[key]
    except Exception:
        return None


def enabled() -> bool:
    """True when the Firebase key is in Streamlit Secrets."""
    return bool(_secret("firebase_api_key"))


def friendly_error(code: str) -> str:
    """Firebase error codes (e.g. 'WEAK_PASSWORD : Password should be...') in plain words."""
    key = str(code).split(":")[0].strip()
    return FIREBASE_ERRORS.get(key, "Something went wrong. Please try again.")


def _valid_email(email: str) -> bool:
    email = str(email or "").strip().lower()
    return bool(_EMAIL.match(email)) and email.endswith("@" + COLLEGE_DOMAIN)


# ---------- Rules (no network, unit tested) ----------

def check_sign_up(name: str, roll: str, email: str, password: str, users: pd.DataFrame) -> str | None:
    """Criteria 7 and 9: XIME email, a password, and a name (and roll number) on the approved list."""
    name, roll, email = str(name or "").strip(), str(roll or "").strip(), str(email or "").strip().lower()
    if not name:
        return MESSAGES["name"]
    if not roll:
        return MESSAGES["roll"]
    if not _valid_email(email):
        return MESSAGES["email"]
    if len(str(password or "")) < MIN_PASSWORD:
        return MESSAGES["password"]
    row = users[users["Name"].str.strip().str.lower() == name.lower()]
    if row.empty:
        return MESSAGES["not_approved"]
    recorded_roll = str(row.iloc[0].get("Roll Number", "")).strip()
    if recorded_roll and recorded_roll != roll:
        return MESSAGES["not_approved"]
    others = users[(users["Name"].str.strip().str.lower() != name.lower())
                   & (users["College Email"].str.strip().str.lower() == email)]
    if not others.empty:
        return MESSAGES["email_taken"]
    return None


def name_for_email(email: str, users: pd.DataFrame) -> str | None:
    match = users[users["College Email"].str.strip().str.lower() == str(email or "").strip().lower()]
    return match.iloc[0]["Name"] if not match.empty else None


# ---------- Firebase calls ----------

def _call(action: str, body: dict) -> tuple[dict, str | None]:
    """POST to Firebase. Returns (data, error_code)."""
    request = urllib.request.Request(_ENDPOINT.format(action=action, key=_secret("firebase_api_key")),
                                     data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read() or b"{}"), None
    except urllib.error.HTTPError as error:
        try:
            return {}, json.loads(error.read()).get("error", {}).get("message", "UNKNOWN")
        except Exception:
            return {}, "UNKNOWN"
    except Exception:
        return {}, "NETWORK"


def create_account(email: str, password: str) -> str | None:
    """Creates the Firebase account and sends the verification email (criterion 7)."""
    data, error = _call("signUp", {"email": email.strip().lower(), "password": password, "returnSecureToken": True})
    if error:
        return friendly_error(error)
    _, error = _call("sendOobCode", {"requestType": "VERIFY_EMAIL", "idToken": data.get("idToken")})
    return friendly_error(error) if error else None


def sign_in(email: str, password: str) -> tuple[str | None, bool, str | None]:
    """(error, verified, id_token). Unverified accounts are refused by the caller (criterion 8)."""
    if not _valid_email(email):
        return MESSAGES["email"], False, None
    data, error = _call("signInWithPassword", {"email": email.strip().lower(), "password": password,
                                               "returnSecureToken": True})
    if error:
        return friendly_error(error), False, None
    token = data.get("idToken")
    info, error = _call("lookup", {"idToken": token})
    if error:
        return friendly_error(error), False, None
    users = info.get("users") or [{}]
    return None, bool(users[0].get("emailVerified")), token


def resend_verification(id_token: str) -> str | None:
    _, error = _call("sendOobCode", {"requestType": "VERIFY_EMAIL", "idToken": id_token})
    return friendly_error(error) if error else None
