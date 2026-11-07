"""Checks for BS-55 sign-up rules. Run with:  python -m pytest tests"""

import pandas as pd

from bookswap.users import check_sign_up, clean_users

USERS = pd.DataFrame(
    [["Krishna", "Builder", "krishna@xime.org"], ["Nandan", "Tester", ""]],
    columns=["Name", "Role", "College Email"],
)


def test_valid_new_student_can_sign_up():
    assert check_sign_up("Ananya Sharma", "ananya@xime.org", USERS) is None


def test_name_and_email_are_required():
    assert "full name" in check_sign_up("  ", "a@xime.org", USERS)
    assert "college email" in check_sign_up("Ananya", "", USERS)


def test_email_must_be_valid_and_from_college():
    assert "valid email" in check_sign_up("Ananya", "ananya@", USERS)
    assert "@xime.org" in check_sign_up("Ananya", "ananya@gmail.com", USERS)


def test_same_name_or_email_cannot_sign_up_twice():
    assert "name already" in check_sign_up("krishna", "new@xime.org", USERS)
    assert "email already" in check_sign_up("Someone New", "KRISHNA@xime.org", USERS)


def test_note_rows_without_a_role_are_ignored():
    rows = pd.DataFrame([["Riya", "Scrum Master", ""], ["Fill the yellow cells...", "", ""]],
                        columns=["Name", "Role", "College Email"])
    assert clean_users(rows)["Name"].tolist() == ["Riya"]
