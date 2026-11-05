"""BookSwap: campus book exchange (XIME PGDM Agile project, Group 2 / Team 3).

Run locally with:  streamlit run app.py

BS-5 (P04-US01): sign in with the Users sheet, see every book with its cover
and title, and open a book to see all its details.
"""

import streamlit as st

from bookswap.data import load_books, load_users
from bookswap.ui import card_html, cover_html, price_text

st.set_page_config(page_title="BookSwap", page_icon="📚", layout="wide")


# ---------- Sign-in (uses the Users sheet) ----------

def sign_in_page() -> None:
    st.title("📚 BookSwap")
    st.write("Swap, lend or sell books with other students on campus.")
    users = load_users()
    with st.form("sign_in"):
        name = st.selectbox("Who are you?", users["Name"].tolist(), index=None, placeholder="Choose your name")
        email = st.text_input("College email", placeholder="name@xime.org")
        submitted = st.form_submit_button("Sign in", type="primary")
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
    left, right = st.columns([1, 2])
    with left:
        st.markdown(cover_html(str(book["Cover Image Link"]), max_width=240), unsafe_allow_html=True)
    with right:
        st.subheader(str(book["Title"]))
        st.write(f"by **{book['Author']}**")
        details = {
            "Course": book["Course"],
            "Genre": book["Genre"],
            "Condition": book["Condition"],
            "Exchange type": book["Exchange Type"],
            "Price": price_text(book),
            "Owner": book["Owner Name"],
            "Status": book["Status"],
            "Book ID": book["Book ID"],
        }
        st.table({"Detail": list(details.keys()), "Value": [str(v) for v in details.values()]})


# ---------- Browse books (US01, acceptance criteria 1, 2 and 4) ----------

def browse_page() -> None:
    books = load_books()
    st.title("📚 Browse books")
    st.caption(f"{len(books)} books listed by students")

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
        st.write(f"Signed in as **{st.session_state['user']}**")
        if st.button("Sign out"):
            del st.session_state["user"]
            st.rerun()
    browse_page()
