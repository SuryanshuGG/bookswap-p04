"""Shared storage for the Sprint 2 tabs (Announcements, Handovers, Messages).

Each tab lives in the same Google Sheet as Books, Users and Requests and is made
with its header row the first time it's needed. Without the Google Sheet secrets
(test mode) rows are kept in memory until the app restarts.
The first column of every tab is its ID, so rows can be found and updated.
"""

import json

import pandas as pd
import streamlit as st


def _secret(key: str):
    try:
        return st.secrets[key]
    except Exception:
        return None


@st.cache_resource(show_spinner=False)
def _worksheet(name: str, columns: tuple):
    sheet_id, key_text = _secret("sheet_id"), _secret("service_account_json")
    if not sheet_id or not key_text:
        raise LookupError("Google Sheet secrets are not set")  # not cached: retried once secrets exist
    import gspread

    sheet = gspread.service_account_from_dict(json.loads(key_text)).open_by_key(sheet_id)
    try:
        return sheet.worksheet(name)
    except gspread.WorksheetNotFound:
        worksheet = sheet.add_worksheet(name, rows=300, cols=len(columns))
        worksheet.append_row(list(columns), value_input_option="RAW")
        return worksheet


@st.cache_resource(show_spinner=False)
def _memory(name: str) -> list:
    return []


def _worksheet_or_none(name: str, columns: list):
    try:
        return _worksheet(name, tuple(columns))
    except Exception:
        return None


def is_permanent(name: str, columns: list) -> bool:
    return _worksheet_or_none(name, columns) is not None


def to_frame(rows: list, columns: list) -> pd.DataFrame:
    padded = [(list(r) + [""] * len(columns))[: len(columns)] for r in rows]
    frame = pd.DataFrame(padded, columns=columns).fillna("").astype(str)
    return frame[frame[columns[0]].str.strip() != ""].reset_index(drop=True)


def load(name: str, columns: list) -> pd.DataFrame:
    worksheet = _worksheet_or_none(name, columns)
    rows = worksheet.get_all_values()[1:] if worksheet is not None else _memory(name)
    return to_frame(rows, columns)


def append(name: str, columns: list, row: list) -> None:
    worksheet = _worksheet_or_none(name, columns)
    if worksheet is not None:
        worksheet.append_row([str(v) for v in row], value_input_option="RAW")
    else:
        _memory(name).append([str(v) for v in row])


def update(name: str, columns: list, row_id: str, changes: dict) -> None:
    """Changes some columns of the row whose first column is row_id."""
    worksheet = _worksheet_or_none(name, columns)
    if worksheet is not None:
        ids = worksheet.col_values(1)
        if row_id in ids:
            number = ids.index(row_id) + 1
            for column, value in changes.items():
                worksheet.update_cell(number, columns.index(column) + 1, str(value))
        return
    for row in _memory(name):
        if row and row[0] == row_id:
            row.extend([""] * (len(columns) - len(row)))
            for column, value in changes.items():
                row[columns.index(column)] = str(value)


def next_id(frame: pd.DataFrame, column: str, prefix: str) -> str:
    numbers = frame[column].str.extract(r"(\d+)")[0].dropna().astype(int) if not frame.empty else []
    return f"{prefix}-{(max(numbers) if len(numbers) else 0) + 1:03d}"
