"""Tests for verified sign-up and sign-in (BS-40, story P04-US09 criteria 7 to 9)."""

import pandas as pd

from bookswap import auth

USERS = pd.DataFrame([["Krishna", "Builder", "", "31106"], ["Riya", "Scrum Master", "riya31blr@xime.org", ""]],
                     columns=["Name", "Role", "College Email", "Roll Number"])


def test_sign_up_needs_xime_email_and_password():  # criterion 7
    assert auth.check_sign_up("Krishna", "31106", "k@gmail.com", "secret12", USERS) == auth.MESSAGES["email"]
    assert auth.check_sign_up("Krishna", "31106", "krishna@xime.org", "123", USERS) == auth.MESSAGES["password"]
    assert auth.check_sign_up("Krishna", "31106", "krishna@xime.org", "secret12", USERS) is None


def test_only_approved_name_and_roll_number():  # criterion 9
    assert auth.check_sign_up("Stranger", "99999", "s@xime.org", "secret12", USERS) == auth.MESSAGES["not_approved"]
    assert auth.check_sign_up("Krishna", "11111", "krishna@xime.org", "secret12", USERS) == auth.MESSAGES["not_approved"]
    assert auth.check_sign_up("Krishna", "31106", "riya31blr@xime.org", "secret12", USERS) == auth.MESSAGES["email_taken"]


def test_unverified_and_wrong_password(monkeypatch):  # criterion 8
    calls = {}

    def fake(action, body):
        calls[action] = body
        if action == "signInWithPassword":
            return ({}, "INVALID_LOGIN_CREDENTIALS") if body["password"] == "wrong" else ({"idToken": "t"}, None)
        if action == "lookup":
            return {"users": [{"emailVerified": False}]}, None
        return {}, None

    monkeypatch.setattr(auth, "_call", fake)
    assert auth.sign_in("krishna@xime.org", "wrong")[0] == "Wrong email or password."
    error, verified, token = auth.sign_in("krishna@xime.org", "secret12")
    assert error is None and verified is False and token == "t"
    assert auth.sign_in("krishna@gmail.com", "secret12")[0] == auth.MESSAGES["email"]


def test_create_account_sends_verification(monkeypatch):  # criterion 7
    calls = []
    monkeypatch.setattr(auth, "_call", lambda action, body: (calls.append((action, body)) or ({"idToken": "t"}, None)))
    assert auth.create_account("krishna@xime.org", "secret12") is None
    assert [a for a, _ in calls] == ["signUp", "sendOobCode"]
    assert calls[1][1] == {"requestType": "VERIFY_EMAIL", "idToken": "t"}


def test_firebase_errors_in_plain_words():
    assert auth.friendly_error("WEAK_PASSWORD : Password should be at least 6 characters").startswith("Use a password")
    assert auth.friendly_error("EMAIL_EXISTS") == auth.FIREBASE_ERRORS["EMAIL_EXISTS"]
