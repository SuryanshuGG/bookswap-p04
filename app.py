"""BookSwap: campus book exchange (XIME PGDM Agile project, Group 2 / Team 3).

Run locally with:  streamlit run app.py

BS-5 (P04-US01): sign in with the Users sheet, see every book with its cover
and title, and open a book to see all its details.
BS-55: new students can sign up with their name and college email.
BS-27 (P04-US03): search books by title or author.
BS-25 (P04-US02): list a book with photo, condition and exchange type.
BS-30 (P04-US04): filter books by course and genre, alone or with search.
"""

import streamlit as st

from bookswap import listings
from bookswap.listings import load_books
from bookswap.filters import NO_FILTER_MATCH_MESSAGE, filter_books
from bookswap.search import NO_MATCH_MESSAGE, search_books
from bookswap.ui import (
    PAGE_CSS, brand_html, card_html, cover_html, details_html, empty_state_html, field_error_html,
    hero_html, listed_html, section_title_html, user_badge_html, welcome_panel_html,
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

def go_to(page: str) -> None:
    st.session_state["page"] = page
    st.rerun()


def top_bar() -> None:
    left, browse, list_book, right, button = st.columns([4, 1.5, 1.6, 2.4, 1.2], vertical_alignment="center")
    with left:
        st.markdown(brand_html(), unsafe_allow_html=True)
    with browse:
        if st.button("Browse books", key="nav_browse", use_container_width=True):
            go_to("browse")
    with list_book:
        if st.button("+ List a book", key="nav_list", use_container_width=True):
            st.session_state.pop("just_listed", None)
            go_to("list")
    with right:
        st.markdown(user_badge_html(st.session_state["user"]), unsafe_allow_html=True)
    with button:
        if st.button("Sign out", use_container_width=True):
            for key in ("user", "page", "just_listed", "listing_errors"):
                st.session_state.pop(key, None)
            st.rerun()


def clear_filters() -> None:
    """Clear button: the full book list returns (acceptance criterion 5)."""
    st.session_state["f_course"] = None
    st.session_state["f_genre"] = None
    st.session_state["f_exchange"] = None


def browse_page() -> None:
    if st.session_state.pop("welcome", False):
        st.success(f"Welcome to BookSwap, {st.session_state['user']}! Your account is ready.")
    books = load_books()
    st.markdown(hero_html(len(books), books["Exchange Type"].value_counts().to_dict()), unsafe_allow_html=True)

    # Search by title or author (BS-27, story P04-US03)
    query = st.text_input(
        "Search books", placeholder="Search by title or author, e.g. Kotler or Habits",
        key="search", label_visibility="collapsed",
    )
    # Filter by course and genre (BS-30, story P04-US04)
    choices = listings.load_choices()
    course_col, genre_col, exchange_col, clear_col = st.columns([2, 2, 1.4, 1], vertical_alignment="bottom")
    with course_col:
        course = st.selectbox("Course", choices["course"], index=None, placeholder="All courses", key="f_course")
    with genre_col:
        genre = st.selectbox("Genre", choices["genre"], index=None, placeholder="All genres", key="f_genre")
    with exchange_col:
        exchange = st.selectbox("Exchange type", listings.EXCHANGE_TYPES, index=None,
                                placeholder="Swap, Lend or Sell", key="f_exchange")
    with clear_col:
        st.button("Clear filters", key="clear_filters", on_click=clear_filters,
                  disabled=not (course or genre or exchange), use_container_width=True)

    shown = filter_books(search_books(books, query), course, genre, exchange)
    if query.strip() or course or genre or exchange:
        label = " · ".join(part for part in (f'"{query.strip()}"' if query.strip() else "", course, genre, exchange) if part)
        st.markdown(section_title_html(f"Results for {label}", f"{len(shown)} found"), unsafe_allow_html=True)
    else:
        st.markdown(section_title_html("All books", f"{len(books)} listed"), unsafe_allow_html=True)
    if shown.empty:
        message = NO_MATCH_MESSAGE if query.strip() and not (course or genre or exchange) else NO_FILTER_MATCH_MESSAGE
        st.markdown(empty_state_html(message), unsafe_allow_html=True)
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


# ---------- List a book (BS-25, story P04-US02) ----------

FORM_KEYS = ["lb_title", "lb_author", "lb_course", "lb_genre", "lb_condition", "lb_exchange", "lb_price"]


def clear_listing_form() -> None:
    for key in FORM_KEYS + ["listing_errors"]:
        st.session_state.pop(key, None)
    # A new key gives an empty photo picker
    st.session_state["photo_key"] = st.session_state.get("photo_key", 0) + 1


def list_book_page() -> None:
    owner = st.session_state["user"]
    if "just_listed" in st.session_state:
        listed_page(st.session_state["just_listed"])
        return
    errors = st.session_state.get("listing_errors", {})
    choices = listings.load_choices()

    _, middle, _ = st.columns([1, 3, 1])
    with middle:
        st.markdown(
            "<div style='font-size:28px;font-weight:800;letter-spacing:-0.6px;margin:10px 0 2px'>List a book</div>"
            f"<div style='font-size:14.5px;color:#5F6368;margin-bottom:14px'>Listing as <b style='color:#1E6B52'>{owner}</b></div>",
            unsafe_allow_html=True,
        )
        if not listings.is_permanent():
            st.caption("Test mode: new listings are kept only until the app restarts.")
        if errors:
            st.error("Please fill the highlighted fields to list your book.")
        with st.container(key="listing_card"):
            st.text_input("Book title *", placeholder="e.g. Marketing Management", key="lb_title")
            field_error(errors, "title")
            st.text_input("Author *", placeholder="e.g. Philip Kotler", key="lb_author")
            field_error(errors, "author")
            course_col, genre_col = st.columns(2)
            with course_col:
                st.selectbox("Course *", choices["course"], index=None, placeholder="Select course", key="lb_course")
                field_error(errors, "course")
            with genre_col:
                st.selectbox("Genre *", choices["genre"], index=None, placeholder="Select genre", key="lb_genre")
                field_error(errors, "genre")
            photo = st.file_uploader(
                "Book photo *", type=["jpg", "jpeg", "png"], key=f"lb_photo_{st.session_state.get('photo_key', 0)}",
                help="Tap to add a photo (JPG or PNG)",
            )
            if photo is None:
                st.caption("Tap Upload to add a photo of the book (JPG or PNG).")
            field_error(errors, "photo")
            st.segmented_control("Condition *", listings.CONDITIONS, key="lb_condition")
            field_error(errors, "condition")
            exchange = st.segmented_control("Exchange type *", listings.EXCHANGE_TYPES, key="lb_exchange")
            field_error(errors, "exchange")
            if exchange == "Sell":
                st.number_input("Price (₹) *", min_value=0, step=10, value=None, placeholder="e.g. 250", key="lb_price")
                field_error(errors, "price")
            else:
                st.caption("Price appears only when you choose Sell.")
            if st.button("Submit listing", key="submit_listing", use_container_width=True):
                submit_listing(owner, photo)


def field_error(errors: dict, field: str) -> None:
    if field in errors:
        st.markdown(field_error_html(errors[field]), unsafe_allow_html=True)


def submit_listing(owner: str, photo) -> None:
    state = st.session_state
    values = {
        "title": state.get("lb_title"), "author": state.get("lb_author"),
        "course": state.get("lb_course"), "genre": state.get("lb_genre"),
        "photo": photo.getvalue() if photo is not None else None,
        "condition": state.get("lb_condition"), "exchange": state.get("lb_exchange"),
        "price": state.get("lb_price"),
    }
    errors = listings.check_listing(values)
    if errors:
        state["listing_errors"] = errors
        st.rerun()
    book_id = listings.next_book_id(load_books())
    row = listings.make_book_row(values, owner, book_id, listings.photo_to_data_uri(values["photo"]))
    listings.save_listing(row)
    clear_listing_form()
    state["just_listed"] = book_id
    st.rerun()


def listed_page(book_id: str) -> None:
    books = load_books()
    match = books[books["Book ID"] == book_id]
    _, middle, _ = st.columns([1, 2, 1])
    with middle:
        if match.empty:
            st.success("Your book is listed!")
        else:
            st.markdown(listed_html(match.iloc[0]), unsafe_allow_html=True)
        back, another = st.columns(2)
        with back:
            if st.button("Back to books", key="back_to_books", use_container_width=True):
                st.session_state.pop("just_listed", None)
                go_to("browse")
        with another:
            if st.button("List another book", key="list_another", use_container_width=True):
                st.session_state.pop("just_listed", None)
                go_to("list")


# ---------- Page flow ----------

if "user" not in st.session_state:
    sign_in_page()
else:
    top_bar()
    if st.session_state.get("page") == "list":
        list_book_page()
    else:
        browse_page()
