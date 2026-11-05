"""BookSwap: campus book exchange (XIME PGDM Agile project, Group 2 / Team 3).

Run locally with:  streamlit run app.py

BS-5 (P04-US01): sign in with the Users sheet, see every book with its cover
and title, and open a book to see all its details.
"""

import streamlit as st

from bookswap.data import load_books, load_users
from bookswap.ui import PAGE_CSS, card_html, cover_html, details_html, hero_html

st.set_page_config(page_title="BookSwap", page_icon="📚", layout="wide")
st.markdown(PAGE_CSS, unsafe_allow_html=True)


# ---------- Sign-in (uses the Users sheet) ----------

def sign_in_page() -> None:
    _, middle, _ = st.columns([1, 2, 1])
    with middle:
        st.markdown(
            hero_html("BookSwap", "Swap, lend or sell books with other students on campus."),
            unsafe_allow_html=True,
        )
        users = load_users()
        with st.form("sign_in"):
            name = st.selectbox("Who are you?", users["Name"].tolist(), index=None, placeholder="Choose your name")
            email = st.text_input("College email", placeholder="name@xime.org")
            submitted = st.form_submit_button("Sign in")
        if submitted:
            if not name:
                st.error("Please choose your name.")
                return
            saved_email = users.loc[users["Name"] == name, "College Email"].iloc[0]
            # Until the Users sheet has everyone's email, choosing a name is enough.
            if saved_email and email.strip().lower() != saved_email.lower():
                st.error("That email doesn't match the one on the Users list.")
                return
            st.session_state["user"] = name
            st.rerun()


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
