"""BookSwap: campus book exchange (XIME PGDM Agile project, Group 2 / Team 3).

Run locally with:  streamlit run app.py

BS-5 (P04-US01): sign in with the Users sheet, see every book with its cover
and title, and open a book to see all its details.
BS-55: new students can sign up with their name and college email.
"""

import streamlit as st

from bookswap.data import load_books
from bookswap.ui import PAGE_CSS, card_html, cover_html, details_html, hero_html
from bookswap.users import add_user, check_sign_up, is_permanent, load_users

st.set_page_config(page_title="BookSwap", page_icon="📚", layout="wide")
st.markdown(PAGE_CSS, unsafe_allow_html=True)


# ---------- Sign-in and sign-up (uses the Users sheet) ----------

def sign_in_form(users) -> None:
    with st.form("sign_in"):
        name = st.selectbox("Who are you?", users["Name"].tolist(), index=None,
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
        st.info("Test mode: new accounts are kept only until the app restarts.")
    with st.form("sign_up", clear_on_submit=False):
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
    _, middle, _ = st.columns([1, 2, 1])
    with middle:
        st.markdown(
            hero_html("BookSwap", "Swap, lend or sell books with other students on campus."),
            unsafe_allow_html=True,
        )
        users = load_users()
        sign_in_tab, sign_up_tab = st.tabs(["Sign in", "New here? Sign up"])
        with sign_in_tab:
            sign_in_form(users)
        with sign_up_tab:
            sign_up_form(users)


# ---------- Book details (US01, acceptance criterion 3) ----------

@st.dialog("Book details", width="large")
def show_details(book) -> None:
    left, right = st.columns([2, 3])
    with left:
        st.markdown(cover_html(str(book["Cover Image Link"]), max_width=240), unsafe_allow_html=True)
    with right:
        st.markdown(details_html(book), unsafe_allow_html=True)


# ---------- Browse books (US01, acceptance criteria 1, 2 and 4) ----------

def browse_page() -> None:
    if st.session_state.pop("welcome", False):
        st.success(f"Welcome to BookSwap, {st.session_state['user']}! Your account is ready.")
    books = load_books()
    st.markdown(
        hero_html("Browse books", f"{len(books)} books listed by students on campus"),
        unsafe_allow_html=True,
    )
    per_row = 4
    for start in range(0, len(books), per_row):
        columns = st.columns(per_row)
        for column, (_, book) in zip(columns, books.iloc[start:start + per_row].iterrows()):
            with column:
                st.markdown(card_html(book), unsafe_allow_html=True)
                if st.button("View details", key=f"view_{book['Book ID']}", use_container_width=True):
                    show_details(book)


# ---------- Page flow ----------

if "user" not in st.session_state:
    sign_in_page()
else:
    with st.sidebar:
        st.markdown(f"Signed in as **{st.session_state['user']}**")
        if st.button("Sign out"):
            del st.session_state["user"]
            st.rerun()
    browse_page()
