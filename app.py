"""BookSwap: campus book exchange (XIME PGDM Agile project, Group 2 / Team 3).

Run locally with:  streamlit run app.py

BS-5 (P04-US01): sign in with the Users sheet, see every book with its cover
and title, and open a book to see all its details.
BS-55: new students can sign up with their name and college email.
"""

import streamlit as st

from bookswap.data import load_books
from bookswap.search import NO_MATCH_MESSAGE, search_books
from bookswap.ui import (
    PAGE_CSS, brand_html, card_html, cover_html, details_html, empty_state_html, hero_html,
    section_title_html, user_badge_html, welcome_panel_html,
)
from bookswap.users import add_user, check_sign_up, is_permanent, load_users

st.set_page_config(page_title="BookSwap", page_icon="📚", layout="wide", initial_sidebar_state="collapsed")
st.markdown(PAGE_CSS, unsafe_allow_html=True)


# ---------- Sign-in and sign-up (uses the Users sheet) ----------

def sign_in_form(users) -> None:
    with st.form("sign_in"):
        name = st.selectbox("Your name", users["Name"].tolist(), index=None,
                            placeholder="Start typing your name")
        email = st.text_input("College email", placeholder="name@xime.org")
        submitted = st.form_submit_button("Sign in")
    if submitted:
        if not name:
            st.error("Please choose your name. New here? Use the Sign up tab.")
            return
        saved_email = users.loc[users["Name"] == name, "College Email"].iloc[0]
        # Until the Users sheet has everyone's email, choosing a name is enough.
        if saved_email and email.strip().lower() != saved_email.lower():
            st.error("That email doesn't match the one on the Users list.")
            return
        st.session_state["user"] = name
        st.rerun()


def sign_up_form(users) -> None:
    if not is_permanent():
        st.caption("Test mode: new accounts are kept only until the app restarts.")
    with st.form("sign_up"):
        name = st.text_input("Full name", placeholder="e.g. Ananya Sharma")
        email = st.text_input("College email", placeholder="name@xime.org", key="sign_up_email")
        submitted = st.form_submit_button("Create account")
    if submitted:
        error = check_sign_up(name, email, users)
        if error:
            st.error(error)
            return
        add_user(name, email)
        st.session_state["user"] = name.strip()
        st.session_state["welcome"] = True
        st.rerun()


def sign_in_page() -> None:
    books = load_books()
    users = load_users()
    st.write("")
    panel, form = st.columns([11, 10], gap="large")
    with panel:
        st.markdown(welcome_panel_html(len(books)), unsafe_allow_html=True)
    with form, st.container(key="auth_card"):
        st.markdown(
            "<div style='font-size:28px;font-weight:800;letter-spacing:-0.6px;margin:0 0 4px'>Welcome</div>"
            "<div style='font-size:15px;color:#5F6368;margin-bottom:16px'>Sign in to browse and request books.</div>",
            unsafe_allow_html=True,
        )
        sign_in_tab, sign_up_tab = st.tabs(["Sign in", "New here? Sign up"])
        with sign_in_tab:
            sign_in_form(users)
        with sign_up_tab:
            sign_up_form(users)


# ---------- Book details (US01, acceptance criterion 3) ----------

@st.dialog(" ", width="large")
def show_details(book) -> None:
    left, right = st.columns([2, 3], gap="large")
    with left:
        st.markdown(cover_html(book, max_width=280, radius=16), unsafe_allow_html=True)
    with right:
        st.markdown(details_html(book), unsafe_allow_html=True)


# ---------- Browse books (US01, acceptance criteria 1, 2 and 4) ----------

def top_bar() -> None:
    left, right, button = st.columns([6, 3, 1], vertical_alignment="center")
    with left:
        st.markdown(brand_html(), unsafe_allow_html=True)
    with right:
        st.markdown(user_badge_html(st.session_state["user"]), unsafe_allow_html=True)
    with button:
        if st.button("Sign out", use_container_width=True):
            del st.session_state["user"]
            st.rerun()


def browse_page() -> None:
    top_bar()
    if st.session_state.pop("welcome", False):
        st.success(f"Welcome to BookSwap, {st.session_state['user']}! Your account is ready.")
    books = load_books()
    st.markdown(hero_html(len(books), books["Exchange Type"].value_counts().to_dict()), unsafe_allow_html=True)

    # Search by title or author (BS-27, story P04-US03)
    query = st.text_input(
        "Search books", placeholder="Search by title or author, e.g. Kotler or Habits",
        key="search", label_visibility="collapsed",
    )
    shown = search_books(books, query)
    if query.strip():
        st.markdown(section_title_html(f'Results for "{query.strip()}"', f"{len(shown)} found"), unsafe_allow_html=True)
    else:
        st.markdown(section_title_html("All books", f"{len(books)} listed"), unsafe_allow_html=True)
    if shown.empty:
        st.markdown(empty_state_html(NO_MATCH_MESSAGE), unsafe_allow_html=True)
        return

    per_row = 4
    for start in range(0, len(shown), per_row):
        columns = st.columns(per_row, gap="medium")
        for column, (_, book) in zip(columns, shown.iloc[start:start + per_row].iterrows()):
            with column:
                with st.container(border=True, key=f"card_{book['Book ID']}"):
                    st.markdown(card_html(book), unsafe_allow_html=True)
                    if st.button("View details", key=f"view_{book['Book ID']}", use_container_width=True):
                        show_details(book)


# ---------- Page flow ----------

if "user" not in st.session_state:
    sign_in_page()
else:
    browse_page()
