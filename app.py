"""BookSwap: campus book exchange (XIME PGDM Agile project, Group 2 / Team 3).

Run locally with:  streamlit run app.py

BS-5 (P04-US01): sign in with the Users sheet, see every book with its cover
and title, and open a book to see all its details.
BS-55: new students can sign up with their name and college email.
BS-27 (P04-US03): search books by title or author.
BS-25 (P04-US02): list a book with photo, condition and exchange type.
BS-30 (P04-US04): filter books by course, genre and exchange type, alone or with search.
BS-31 (P04-US05): request a book; swap offers, pay-at-handover note, My Requests.
BS-36 and BS-56 (P04-US07): My Listings with Accept and Decline, return dates, badges, edit, pause and delete.
"""

from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from bookswap import listings
from bookswap import requests as book_requests
from bookswap import help as book_help
from bookswap import wishlist
from bookswap import announcements
from bookswap import handover
from bookswap import reviews
from bookswap import donations
from bookswap import ratings
from bookswap.listings import load_books
from bookswap.filters import NO_FILTER_MATCH_MESSAGE, filter_books
from bookswap.search import NO_MATCH_MESSAGE, search_books
from bookswap.ui import (
    PAGE_CSS, brand_html, card_html, cover_html, details_html, empty_state_html, field_error_html,
    hero_html, listed_html, listing_header_html, note_html, owner_request_html, request_label_html, request_row_html, request_sent_html,
    section_title_html, user_badge_html, splash_html, onboarding_html, auth_heading_html, auth_panel_html,
    help_page_html, wish_row_html, announcements_html, handover_card_html, message_html,
    rating_line_html, review_html, profile_html,
)
from bookswap.users import add_user, check_sign_in, check_sign_up, is_permanent, load_users

st.set_page_config(page_title="BookSwap", page_icon="assets/logo.png", layout="wide", initial_sidebar_state="collapsed")
st.markdown(PAGE_CSS, unsafe_allow_html=True)


# ---------- Sign-in and sign-up (uses the Users sheet) ----------

def sign_in_form(users) -> None:
    with st.form("sign_in"):
        name = st.selectbox("Your name", users["Name"].tolist(), index=None,
                            placeholder="Start typing your name")
        email = st.text_input("College email", placeholder="name@xime.org")
        submitted = st.form_submit_button("Sign in")
    if submitted:
        # A college email ending in @xime.org is always required (BS-55 fix)
        error = check_sign_in(name, email, users)
        if error:
            st.error(error)
            return
        st.session_state["user"] = name
        st.rerun()


def storage_note() -> None:
    """Shows why the app is in test mode, so the team can fix the Google Sheet secrets."""
    reason = listings.storage_problem()
    if reason:
        st.caption(f"Not saving to the Google Sheet because {reason}.")


def sign_up_form(users) -> None:
    if not is_permanent():
        st.caption("Test mode: new accounts are kept only until the app restarts.")
        storage_note()
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


def go_auth(step) -> None:
    st.session_state["auth_step"] = step


def splash_page() -> None:
    """First page: only the logo, name and one line, then Get started or Sign in. No book counts."""
    _, mid, _ = st.columns([1, 1.15, 1])
    with mid, st.container(key="splash_card"):
        st.markdown(splash_html(), unsafe_allow_html=True)
        st.button("Get started", key="get_started", use_container_width=True, on_click=go_auth, args=(0,))
        st.button("I already have an account", key="have_account", use_container_width=True, on_click=go_auth, args=("signin",))
        st.markdown("<div style='text-align:center;font-size:12.5px;color:#1F2A26;margin-top:4px'>For XIME Bangalore students</div>",
                    unsafe_allow_html=True)


def intro_page(step: int) -> None:
    """Three short intro steps with Back, Skip, Next and progress dots."""
    _, mid, _ = st.columns([1, 1.15, 1])
    with mid, st.container(key="onboard_card"):
        back, _, skip = st.columns([1.4, 1, 1], vertical_alignment="center")
        with back:
            st.button("← Back", key="intro_back", on_click=go_auth, args=(step - 1 if step else "splash",))
        with skip:
            if step < 2:
                st.button("Skip", key="intro_skip", on_click=go_auth, args=("signup",))
        st.markdown(onboarding_html(step), unsafe_allow_html=True)
        if step < 2:
            st.button("Next →", key="intro_next", use_container_width=True, on_click=go_auth, args=(step + 1,))
        else:
            st.button("Create account", key="intro_join", use_container_width=True, on_click=go_auth, args=("signup",))
            st.button("Sign in", key="intro_signin", use_container_width=True, on_click=go_auth, args=("signin",))


def auth_page(mode: str) -> None:
    """Separate page after tapping Sign in or Sign up, with the Welcome heading."""
    users = load_users()
    panel, form = st.columns([1.05, 1], gap="large")
    with panel:
        st.markdown(auth_panel_html(), unsafe_allow_html=True)
    with form, st.container(key="auth_card"):
        st.button("← Back", key="auth_back", on_click=go_auth, args=("splash",))
        st.markdown(auth_heading_html(mode), unsafe_allow_html=True)
        if mode == "signup":
            sign_up_form(users)
            st.button("Already have an account? Sign in", key="auth_switch", on_click=go_auth, args=("signin",))
        else:
            sign_in_form(users)
            st.button("New here? Create account", key="auth_switch", on_click=go_auth, args=("signup",))


def sign_in_page() -> None:
    step = st.session_state.get("auth_step", "splash")
    if step in ("signin", "signup"):
        auth_page(step)
    elif isinstance(step, int):
        intro_page(step)
    else:
        splash_page()


# ---------- Book details (US01, acceptance criterion 3) ----------

@st.dialog(" ", width="large")
def show_details(book) -> None:
    left, right = st.columns([2, 3], gap="large")
    with left:
        st.markdown(cover_html(book, max_width=280, radius=16), unsafe_allow_html=True)
    with right:
        st.markdown(details_html(book), unsafe_allow_html=True)
        avg, count = ratings.average(ratings.load(), book["Owner Name"])
        st.markdown(rating_line_html(book["Owner Name"], avg, count), unsafe_allow_html=True)
        request_section(book)
    reviews_section(book)
    report_section(book)


# ---------- Request a book (BS-31, story P04-US05) ----------

def request_section(book) -> None:
    """The Request button and its four states from Swasti's BS-32 design."""
    user = st.session_state["user"]
    requests = book_requests.load_requests()
    state = book_requests.request_state(book, user, requests)
    if state == "own":
        st.markdown(request_label_html("This is your book", book_requests.MESSAGES["own"], mint=True), unsafe_allow_html=True)
        return
    if state == "unavailable":
        if book["Status"] == "Donated":  # BS-51, US14 criterion 3
            st.markdown(request_label_html("Donated to the library", donations.MESSAGES["unavailable_to_others"]),
                        unsafe_allow_html=True)
            return
        st.markdown(request_label_html("Not available", book_requests.MESSAGES["unavailable"]), unsafe_allow_html=True)
        return
    if state == "requested":
        st.markdown(request_label_html("✓ Requested", book_requests.MESSAGES["requested"]), unsafe_allow_html=True)
        return

    offered = None
    if book["Exchange Type"] == "Swap":
        offer = book_requests.books_to_offer(load_books(), user)
        if offer.empty:
            st.markdown(request_label_html("List a book to swap", book_requests.MESSAGES["no_books_to_offer"]), unsafe_allow_html=True)
            if st.button("+ List a book", key="swap_list_first", use_container_width=True):
                st.session_state.pop("just_listed", None)
                go_to("list")
            return
        titles = dict(zip(offer["Book ID"], offer["Title"]))
        offered = st.selectbox("Book you offer in return *", list(titles), index=None,
                               format_func=lambda bid: titles[bid], placeholder="Choose one of your books",
                               key=f"offer_{book['Book ID']}")
    elif book["Exchange Type"] == "Sell":
        st.markdown(note_html(book_requests.pay_note(book)), unsafe_allow_html=True)

    if st.button("Request this book", key="request_book", use_container_width=True):
        books = load_books()
        error = book_requests.check_request(book, user, book_requests.load_requests(), books, offered)
        if error:
            st.error(error)
            return
        request_id = book_requests.next_request_id(book_requests.load_requests())
        book_requests.save_request(book_requests.make_request_row(request_id, book["Book ID"], user, offered))
        st.session_state["just_requested"] = request_id
        st.session_state["page"] = "requests"
        st.rerun()


def offered_title(offered_id: str) -> str:
    books = load_books()
    match = books[books["Book ID"] == offered_id]
    return match.iloc[0]["Title"] if not match.empty else offered_id


def request_extra(row) -> str:
    """Swap offer, payment line or return date shown under a request."""
    if row.get("Return Date"):
        return f"Return by {pd.to_datetime(row['Return Date']).strftime('%-d %b %Y')}"
    if row.get("Exchange Type") == "Swap" and row.get("Offered Book ID"):
        books = load_books()
        match = books[books["Book ID"] == row["Offered Book ID"]]
        title = match.iloc[0]["Title"] if not match.empty else row["Offered Book ID"]
        return f"You offer: {title}"
    if row.get("Exchange Type") == "Sell":
        return book_requests.pay_note(row)
    return ""


def request_sent_page(request_id: str) -> None:
    mine = book_requests.my_requests(book_requests.load_requests(), load_books(), st.session_state["user"])
    match = mine[mine["Request ID"] == request_id]
    _, middle, _ = st.columns([1, 2, 1])
    with middle:
        if match.empty:
            st.success("Request sent!")
        else:
            row = match.iloc[0]
            st.markdown(request_sent_html(row, row["Owner Name"], request_extra(row)), unsafe_allow_html=True)
        view, back = st.columns(2)
        with view:
            if st.button("View My Requests", key="view_my_requests", use_container_width=True):
                st.session_state.pop("just_requested", None)
                go_to("requests")
        with back:
            if st.button("Back to books", key="sent_back", use_container_width=True):
                st.session_state.pop("just_requested", None)
                go_to("browse")


def mark_requests_seen() -> None:
    """Opening My Requests clears its badge (US07 criterion 8). Runs before the top bar is drawn."""
    user = st.session_state["user"]
    requests = book_requests.load_requests()
    unseen = requests[(requests["Requester Name"].str.lower() == user.lower())
                      & requests["Status"].isin(["Accepted", "Declined"]) & (requests["Seen By Requester"] != "yes")]
    book_requests.update_requests({rid: {"Seen By Requester": "yes"} for rid in unseen["Request ID"]})


def my_requests_page() -> None:
    if "just_requested" in st.session_state:
        request_sent_page(st.session_state["just_requested"])
        return
    mine = book_requests.my_requests(book_requests.load_requests(), load_books(), st.session_state["user"])
    _, middle, _ = st.columns([1, 3, 1])
    with middle:
        st.markdown(
            "<div style='font-size:28px;font-weight:800;letter-spacing:-0.6px;margin:10px 0 14px'>My Requests</div>",
            unsafe_allow_html=True,
        )
        if not book_requests.is_permanent():
            st.caption("Test mode: requests are kept only until the app restarts.")
        if mine.empty:
            st.markdown(empty_state_html("You haven't requested any books yet."), unsafe_allow_html=True)
            if st.button("Browse books", key="empty_browse", use_container_width=True):
                go_to("browse")
            return
        tabs = [f"All ({len(mine)})", "Pending", "Accepted", "Declined"]
        choice = st.segmented_control("Show", tabs, default=tabs[0], key="req_tab", label_visibility="collapsed")
        shown = mine if not choice or choice.startswith("All") else mine[mine["Status"] == choice]
        if shown.empty:
            st.markdown(empty_state_html(f"No {choice.lower()} requests."), unsafe_allow_html=True)
        for _, row in shown.iterrows():
            st.markdown(request_row_html(row, request_extra(row)), unsafe_allow_html=True)
            if row["Status"] == "Accepted":
                handover_panel(row["Request ID"])


# ---------- Browse books (US01, acceptance criteria 1, 2 and 4) ----------

def go_to(page: str) -> None:
    st.session_state["page"] = page
    st.rerun()


def top_bar() -> None:
    user = st.session_state["user"]
    requests, books = book_requests.load_requests(), load_books()
    owner_count = book_requests.owner_badge(requests, books, user)
    requester_count = book_requests.requester_badge(requests, user)
    wish_count = wishlist.badge_count(wishlist.load_wishes(), books, user)
    left, browse, list_book, my_list, my_req, wish, helps, right, button = st.columns(
        [1.9, 1.6, 1.5, 1.6, 1.6, 1.3, 0.9, 1.6, 1.3], vertical_alignment="center")
    with left:
        st.markdown(brand_html(), unsafe_allow_html=True)
    with browse:
        if st.button("Browse books", key="nav_browse", use_container_width=True):
            go_to("browse")
    with list_book:
        if st.button("+ List a book", key="nav_list", use_container_width=True):
            st.session_state.pop("just_listed", None)
            go_to("list")
    with my_list:
        # Badge: new requests on my books (US07 criterion 8)
        label = f"My Listings ({owner_count})" if owner_count else "My Listings"
        if st.button(label, key="nav_listings", use_container_width=True):
            go_to("listings")
    with my_req:
        # Badge: my requests accepted or declined since I last looked (US07 criterion 8)
        label = f"My Requests ({requester_count})" if requester_count else "My Requests"
        if st.button(label, key="nav_requests", use_container_width=True):
            st.session_state.pop("just_requested", None)
            go_to("requests")
    with wish:
        # Badge: books on my wishlist that someone has now listed (US10 criterion 6)
        label = f"Wishlist ({wish_count})" if wish_count else "Wishlist"
        if st.button(label, key="nav_wishlist", use_container_width=True):
            go_to("wishlist")
    with helps:
        # Guidelines and how-to one tap from every screen (US11 criterion 4)
        if st.button("Help", key="nav_help", use_container_width=True):
            go_to("help")
    with right:
        st.markdown(user_badge_html(st.session_state["user"]), unsafe_allow_html=True)
        if st.button("My profile", key="nav_profile", use_container_width=True):
            go_to("profile")
        # Coordinator tools: announcements, donations and reports (US13, US14, US09)
        if announcements.is_coordinator(user, load_users()):
            if st.button("Coordinator", key="nav_coordinator", use_container_width=True):
                go_to("coordinator")
    with button:
        if st.button("Sign out", use_container_width=True):
            for key in ("user", "auth_step", "page", "just_listed", "listing_errors", "just_requested", "req_tab", "listing_message", "wish_message", "coord_message"):
                st.session_state.pop(key, None)
            st.rerun()


def clear_filters() -> None:
    """Clear button: the full book list returns (acceptance criterion 5)."""
    st.session_state["f_course"] = None
    st.session_state["f_genre"] = None
    st.session_state["f_exchange"] = None


# ---------- My Listings (BS-36 and BS-56, story P04-US07) ----------

def owner_extra(row) -> str:
    if row.get("Exchange Type") == "Swap" and row.get("Offered Book ID"):
        return f"Offers in return: {offered_title(row['Offered Book ID'])}"
    if row.get("Exchange Type") == "Sell":
        return book_requests.collect_note(row)
    if row.get("Return Date"):
        return f"Return by {pd.to_datetime(row['Return Date']).strftime('%-d %b %Y')}"
    return ""


def answer(request_id: str, accept: bool, return_date=None) -> None:
    requests, books = book_requests.load_requests(), load_books()
    error, request_changes, book_changes = book_requests.plan_answer(
        requests, books, request_id, st.session_state["user"], accept, return_date)
    if error:
        st.session_state["listing_message"] = ("error", error)
        return
    book_requests.update_requests(request_changes)
    if book_changes:
        book_id = requests[requests["Request ID"] == request_id].iloc[0]["Book ID"]
        listings.update_book(book_id, book_changes)
    st.session_state["listing_message"] = ("success", "Request accepted. The book is now Reserved." if accept else "Request declined.")


def my_listings_page() -> None:
    user = st.session_state["user"]
    books = load_books()
    mine = books[(books["Owner Name"].str.lower() == user.lower()) & (books["Status"] != "Deleted")]
    on_mine = book_requests.requests_for_owner(book_requests.load_requests(), books, user)
    _, middle, _ = st.columns([1, 3, 1])
    with middle:
        st.markdown("<div style='font-size:28px;font-weight:800;letter-spacing:-0.6px;margin:10px 0 14px'>My Listings</div>",
                    unsafe_allow_html=True)
        kind, text = st.session_state.pop("listing_message", (None, None))
        if kind == "error":
            st.error(text)
        elif kind == "success":
            st.success(text)
        if mine.empty:
            st.markdown(empty_state_html("You haven't listed any books yet."), unsafe_allow_html=True)
            if st.button("+ List a book", key="empty_list", use_container_width=True):
                go_to("list")
            return
        for _, book in mine.iterrows():
            book_id = book["Book ID"]
            book_requests_here = on_mine[on_mine["Book ID"] == book_id] if not on_mine.empty else on_mine
            pending = book_requests_here[book_requests_here["Status"] == "Pending"] if not book_requests_here.empty else book_requests_here
            with st.container(key=f"mylisting_{book_id}"):
                st.markdown(listing_header_html(book, len(pending)), unsafe_allow_html=True)
                # Requests on this book: Accept or Decline (BS-36)
                for _, req in book_requests_here.iterrows():
                    st.markdown(owner_request_html(req, owner_extra(req)), unsafe_allow_html=True)
                    if req["Status"] == "Accepted":
                        handover_panel(req["Request ID"])
                    if req["Status"] != "Pending":
                        continue
                    rid = req["Request ID"]
                    return_date = None
                    if book["Exchange Type"] == "Lend":
                        return_date = st.date_input(
                            "Return date *", value=date.today() + timedelta(days=14), min_value=date.today() + timedelta(days=1),
                            max_value=date.today() + timedelta(days=book_requests.MAX_LEND_DAYS), key=f"return_{rid}",
                            format="DD/MM/YYYY")
                    yes, no = st.columns(2)
                    with yes:
                        st.button("Accept", key=f"accept_{rid}", use_container_width=True,
                                  on_click=answer, args=(rid, True, return_date))
                    with no:
                        st.button("Decline", key=f"decline_{rid}", use_container_width=True,
                                  on_click=answer, args=(rid, False))
                # Edit, pause or delete the listing (BS-56)
                has_pending = not pending.empty
                if book["Status"] in ("Available", "Paused"):
                    with st.expander("Edit listing"):
                        condition = st.selectbox("Condition", listings.CONDITIONS,
                                                 index=listings.CONDITIONS.index(book["Condition"]) if book["Condition"] in listings.CONDITIONS else 0,
                                                 key=f"edit_cond_{book_id}")
                        kind_choice = st.selectbox("Exchange type", listings.EXCHANGE_TYPES,
                                                   index=listings.EXCHANGE_TYPES.index(book["Exchange Type"]), key=f"edit_type_{book_id}")
                        price = None
                        if kind_choice == "Sell":
                            current = book["Price (Rs)"]
                            price = st.number_input("Price (₹)", min_value=0, step=10,
                                                    value=int(current) if pd.notna(current) and str(current) != "" else 0,
                                                    key=f"edit_price_{book_id}")
                        if st.button("Save changes", key=f"save_{book_id}", use_container_width=True):
                            errors = listings.check_edit(book, user, condition, kind_choice, price)
                            if errors:
                                st.error(" ".join(errors.values()))
                            else:
                                listings.update_book(book_id, listings.edit_changes(condition, kind_choice, price))
                                st.session_state["listing_message"] = ("success", f"Saved changes to {book['Title']}.")
                                st.rerun()
                    pause_col, delete_col = st.columns(2)
                    with pause_col:
                        label = "Resume listing" if book["Status"] == "Paused" else "Pause listing"
                        if st.button(label, key=f"pause_{book_id}", use_container_width=True):
                            error, changes = listings.pause_change(book, user, has_pending)
                            if error:
                                st.session_state["listing_message"] = ("error", error)
                            else:
                                listings.update_book(book_id, changes)
                                st.session_state["listing_message"] = (
                                    "success", f"{book['Title']} is {'hidden from browsing' if changes['Status'] == 'Paused' else 'listed again'}.")
                            st.rerun()
                    with delete_col:
                        if st.button("Delete listing", key=f"delete_{book_id}", use_container_width=True):
                            error, changes = listings.delete_change(book, user, has_pending)
                            if error:
                                st.session_state["listing_message"] = ("error", error)
                            else:
                                listings.update_book(book_id, changes)
                                st.session_state["listing_message"] = ("success", f"Deleted {book['Title']}.")
                            st.rerun()
                if book["Status"] == "Available":
                    # Donate to the department library (BS-51, US14 criterion 1)
                    if st.button("Donate to the library", key=f"donate_{book_id}", use_container_width=True):
                        error, message, changes = donations.donate(book, user, has_pending)
                        if not error:
                            listings.update_book(book_id, changes)
                        st.session_state["listing_message"] = ("error", error) if error else ("success", message)
                        st.rerun()
                elif book["Status"] == "Donated":
                    st.caption("Donated · waiting for the coordinator to collect it. You can withdraw until then.")
                    if st.button("Withdraw donation", key=f"withdraw_{book_id}", use_container_width=True):
                        error, message, changes = donations.withdraw(book, user)
                        if not error:
                            listings.update_book(book_id, changes)
                        st.session_state["listing_message"] = ("error", error) if error else ("success", message)
                        st.rerun()
                elif book["Status"] == "Closed":
                    st.caption("Received by the department library. This listing is closed.")


def browse_page() -> None:
    if st.session_state.pop("welcome", False):
        st.success(f"Welcome to BookSwap, {st.session_state['user']}! Your account is ready.")
    books = listings.visible_books(load_books())
    # Return reminders for borrowed books (BS-39, US08 criteria 7 and 8)
    for note in handover.reminders(book_requests.load_requests(), load_books(), handover.load(), st.session_state["user"]):
        (st.error if note.startswith("Overdue") else st.warning)(note)
    # Reading circle announcements on the home screen, soonest first (BS-49, US13)
    st.markdown(announcements_html(announcement_cards(announcements.live(announcements.load()))),
                unsafe_allow_html=True)
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
        if query.strip() and not (course or genre or exchange):
            _, middle, _ = st.columns([1, 2, 1])
            with middle:
                st.button(f'+ Add "{query.strip()}" to my wishlist', key="wish_from_search", use_container_width=True,
                          on_click=add_to_wishlist, args=(query.strip(), ""))
                show_wish_message()
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
            storage_note()
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


# ---------- Wishlist (BS-42, story P04-US10) ----------

def add_to_wishlist(title: str, author: str) -> None:
    error = wishlist.add_wish(title, author, st.session_state["user"])
    st.session_state["wish_message"] = ("error", error) if error else ("success", wishlist.MESSAGES["saved"])


def remove_from_wishlist(wish_id: str) -> None:
    wishlist.remove_wish(wish_id, st.session_state["user"])
    st.session_state["wish_message"] = ("success", wishlist.MESSAGES["removed"])


def show_wish_message() -> None:
    kind, text = st.session_state.pop("wish_message", (None, None))
    if kind == "error":
        st.warning(text)
    elif kind == "success":
        st.success(text)


def wishlist_page() -> None:
    user = st.session_state["user"]
    books = load_books()
    mine = wishlist.with_matches(wishlist.my_wishes(wishlist.load_wishes(), user), books, user)
    _, middle, _ = st.columns([1, 3, 1])
    with middle:
        st.markdown("<div style='font-size:28px;font-weight:800;letter-spacing:-0.6px;margin:10px 0 4px'>My Wishlist</div>"
                    "<div style='color:#5F6368;font-size:15px;margin-bottom:14px'>Save a book you can't find. "
                    "It shows Now Available as soon as another student lists it.</div>", unsafe_allow_html=True)
        if not wishlist.is_permanent():
            st.caption("Test mode: wishlist entries are kept only until the app restarts.")
        with st.form("add_wish", clear_on_submit=True, border=True):
            title_col, author_col = st.columns([3, 2])
            with title_col:
                title = st.text_input("Book title *", placeholder="e.g. Principles of Corporate Finance")
            with author_col:
                author = st.text_input("Author (optional)", placeholder="e.g. Brealey")
            if st.form_submit_button("+ Add to wishlist", use_container_width=True):
                add_to_wishlist(title, author)
                st.rerun()  # redraw so the Wishlist badge in the top bar counts the new book
        show_wish_message()
        if mine.empty:
            st.markdown(empty_state_html("Your wishlist is empty. Add a book above, or from a search that finds nothing."),
                        unsafe_allow_html=True)
            return
        ready = int(mine["Now Available"].sum())
        st.markdown(section_title_html("Saved books", f"{len(mine)} saved · {ready} now available"), unsafe_allow_html=True)
        for _, wish in mine.iterrows():
            with st.container(key=f"wish_{wish['Wish ID']}"):
                added = pd.to_datetime(wish["Date Added"], errors="coerce")
                st.markdown(wish_row_html(wish["Title"], wish["Author"], added.strftime("%-d %b %Y") if pd.notna(added) else wish["Date Added"], wish["Now Available"],
                                          len(wish["Match IDs"])), unsafe_allow_html=True)
                view, remove = st.columns(2)
                with view:
                    if wish["Now Available"]:
                        match = books[books["Book ID"] == wish["Match IDs"][0]].iloc[0]
                        if st.button("View book", key=f"wish_view_{wish['Wish ID']}", use_container_width=True):
                            show_details(match)
                with remove:
                    st.button("Remove", key=f"wish_remove_{wish['Wish ID']}", use_container_width=True,
                              on_click=remove_from_wishlist, args=(wish["Wish ID"],))


# ---------- Help: guidelines and how-to (BS-44, BS-45, story P04-US11) ----------

def help_page() -> None:
    _, middle, _ = st.columns([1, 3, 1])
    with middle:
        st.markdown(help_page_html(book_help.GUIDELINES, book_help.HOW_TO, book_help.HANDOVER_POINTS,
                                   book_help.HANDOVER_HOURS), unsafe_allow_html=True)


# ---------- Reading circle announcements (BS-49, story P04-US13) ----------

def announcement_cards(rows) -> list[dict]:
    cards = []
    for _, a in rows.iterrows():
        when = pd.to_datetime(a["Event Date"], errors="coerce")
        at = pd.to_datetime(a["Event Time"], format="%H:%M", errors="coerce")
        cards.append({"title": a["Title"], "venue": a["Venue"], "details": a["Details"],
                      "date_text": when.strftime("%a %-d %b") if pd.notna(when) else a["Event Date"],
                      "time_text": at.strftime("%-I:%M %p").lower() if pd.notna(at) else a["Event Time"]})
    return cards


def remove_announcement(announcement_id: str) -> None:
    error = announcements.remove(announcement_id, st.session_state["user"], load_users())
    st.session_state["coord_message"] = ("error", error) if error else ("success", announcements.MESSAGES["deleted"])


def coordinator_page() -> None:
    user, users = st.session_state["user"], load_users()
    _, middle, _ = st.columns([1, 3, 1])
    with middle:
        st.markdown("<div style='font-size:28px;font-weight:800;letter-spacing:-0.6px;margin:10px 0 4px'>Coordinator</div>"
                    "<div style='color:#5F6368;font-size:15px;margin-bottom:14px'>Literary club tools: donations, reports and "
                    "reading circle announcements.</div>", unsafe_allow_html=True)
        if not announcements.is_coordinator(user, users):  # criterion 5
            st.warning(announcements.MESSAGES["not_coordinator"])
            return
        if not announcements.is_permanent():
            st.caption("Test mode: announcements are kept only until the app restarts.")
        st.markdown(section_title_html("Post a reading circle announcement", "Shows on every student's home screen"),
                    unsafe_allow_html=True)
        with st.form("post_announcement", clear_on_submit=True, border=True):
            title = st.text_input("Title *", placeholder="e.g. Reading circle: Atomic Habits")
            day_col, time_col = st.columns(2)
            with day_col:
                event_date = st.date_input("Date *", value=None, min_value=announcements.today_ist(), format="DD/MM/YYYY")
            with time_col:
                event_time = st.time_input("Time *", value=None, step=900)
            venue = st.text_input("Venue *", placeholder="e.g. Library discussion room")
            details = st.text_area("Details (optional)", max_chars=200, placeholder="e.g. Chapters 1 to 4. All welcome.")
            if st.form_submit_button("Post announcement", use_container_width=True):
                error = announcements.post(title, event_date, event_time, venue, details, user, users)
                st.session_state["coord_message"] = ("error", error) if error else ("success", announcements.MESSAGES["posted"])
                st.rerun()
        kind, text = st.session_state.pop("coord_message", (None, None))
        if kind == "error":
            st.warning(text)
        elif kind == "success":
            st.success(text)
        donations_section()
        reports_section()
        upcoming = announcements.live(announcements.load())
        st.markdown(section_title_html("Live announcements", f"{len(upcoming)} shown to students · past events hide automatically"),
                    unsafe_allow_html=True)
        for card, (_, row) in zip(announcement_cards(upcoming), upcoming.iterrows()):
            st.markdown(announcements_html([card]), unsafe_allow_html=True)
            st.button("Remove", key=f"ann_remove_{row['Announcement ID']}", on_click=remove_announcement,
                      args=(row["Announcement ID"],))


# ---------- Handover after Accept (BS-39, story P04-US08) ----------

def _handover_message(request_id: str, kind: str, text: str) -> None:
    st.session_state[f"handover_msg_{request_id}"] = (kind, text)


def _request_and_book(request_id: str):
    requests, books = book_requests.load_requests(), load_books()
    req = requests[requests["Request ID"] == request_id].iloc[0]
    book = books[books["Book ID"] == req["Book ID"]].iloc[0]
    return req, book


def confirm_handover(request_id: str) -> None:
    req, book = _request_and_book(request_id)
    plan = handover.find(handover.load(), request_id)
    error, changes, book_changes, offered_changes = handover.plan_confirm(plan, req, book, st.session_state["user"])
    if error:
        return _handover_message(request_id, "error", error)
    handover.save_changes(request_id, changes)
    if book_changes:
        listings.update_book(book["Book ID"], book_changes)
    if offered_changes and req.get("Offered Book ID"):
        listings.update_book(req["Offered Book ID"], offered_changes)
    _handover_message(request_id, "success", "Handover complete. The book is now Exchanged." if book_changes
                      else "Thanks. Waiting for the other student to confirm.")


def mark_paid(request_id: str) -> None:
    req, book = _request_and_book(request_id)
    error, changes = handover.plan_paid(handover.find(handover.load(), request_id), req, book, st.session_state["user"])
    if error:
        return _handover_message(request_id, "error", error)
    handover.save_changes(request_id, changes)
    _handover_message(request_id, "success", f"Marked Paid ₹{changes['Paid Amount']}.")


def mark_returned(request_id: str) -> None:
    req, book = _request_and_book(request_id)
    error, changes, book_changes = handover.plan_returned(handover.find(handover.load(), request_id), req, book,
                                                          st.session_state["user"])
    if error:
        return _handover_message(request_id, "error", error)
    handover.save_changes(request_id, changes)
    listings.update_book(book["Book ID"], book_changes)
    _handover_message(request_id, "success", f"{book['Title']} is back and listed as Available again.")


def handover_panel(request_id: str) -> None:
    """Plan, confirm and finish the handover. Both students see the same card (criterion 5)."""
    user = st.session_state["user"]
    req, book = _request_and_book(request_id)
    role = handover.role_of(user, req, book)
    if role is None:
        return
    plan = handover.find(handover.load(), request_id)
    other = req["Requester Name"] if role == "owner" else book["Owner Name"]
    scheduled, done = handover.is_scheduled(plan), handover.both_done(plan)
    plan_text = where = proposer = ""
    if scheduled:
        when = datetime.combine(date.fromisoformat(plan["Date"]), datetime.strptime(plan["Time"], "%H:%M").time())
        plan_text = f"{plan['Point']} · {when.strftime('%a %-d %b, %-I:%M %p').replace('AM', 'am').replace('PM', 'pm')}"
        where, proposer = handover.point_where(plan["Point"]), plan.get("Proposed By", "")
    you_done = scheduled and plan.get("Owner Done" if role == "owner" else "Requester Done") == "yes"
    they_done = scheduled and plan.get("Requester Done" if role == "owner" else "Owner Done") == "yes"
    steps = [("You confirmed", you_done), (f"{other} confirmed", they_done)] if scheduled else []
    outcome, tone = "", "good"
    if done:
        outcome = "Exchanged ✓ Both of you confirmed the handover."
        if book["Exchange Type"] == "Sell":
            amount = plan.get("Paid Amount") or (str(int(float(book["Price (Rs)"]))) if str(book["Price (Rs)"]) not in ("", "nan") else "")
            outcome += f" · Paid ₹{amount}" if plan.get("Paid") == "yes" else f" · Payment of ₹{amount} not marked yet"
        if book["Exchange Type"] == "Lend":
            status = handover.lend_status(req, plan, handover.now_ist().date())
            due = pd.to_datetime(req["Return Date"]).strftime("%-d %b")
            outcome = {"Returned": "Returned ✓ The book is Available again.", "Overdue": f"Overdue: was due back on {due}.",
                       "Due soon": f"On loan · due back on {due} (in 2 days or less)."}.get(status, f"On loan · due back on {due}.")
            tone = {"Overdue": "bad", "Due soon": "warn"}.get(status, "good")
    elif scheduled and you_done:
        outcome, tone = f"Waiting for {other} to confirm. The book stays Reserved until then.", "warn"
    with st.container(key=f"handover_{request_id}"):
        st.markdown(handover_card_html(plan_text, where, proposer, steps, outcome, tone), unsafe_allow_html=True)
        kind, text = st.session_state.pop(f"handover_msg_{request_id}", (None, None))
        if kind == "error":
            st.warning(text)
        elif kind == "success":
            st.success(text)
        if not done:
            if scheduled and not you_done:
                st.button("✓ Handover done", key=f"confirm_{request_id}", use_container_width=True,
                          on_click=confirm_handover, args=(request_id,))
            with st.expander("Change point or time" if scheduled else "Choose point and time", expanded=not scheduled):
                with st.form(f"plan_{request_id}", border=False):
                    names = handover.handover_point_names()
                    point = st.selectbox("Handover point *", names, index=names.index(plan["Point"]) if scheduled else None,
                                         placeholder="Choose an approved campus point")
                    day_col, time_col = st.columns(2)
                    with day_col:
                        day = st.date_input("Date *", value=None, min_value=handover.now_ist().date(), format="DD/MM/YYYY")
                    with time_col:
                        at = st.time_input("Time *", value=None, step=900)
                    st.caption("Approved points only, between 8:00 am and 8:00 pm. Changing the plan clears both confirmations.")
                    if st.form_submit_button("Save handover plan", use_container_width=True):
                        error = handover.check_schedule(point, day, at)
                        if error:
                            _handover_message(request_id, "error", error)
                        else:
                            handover.save_schedule(request_id, point, day, at, user)
                            handover.send_message(request_id, user, f"Planned the handover: {point}, "
                                                  f"{day.strftime('%-d %b')} at {at.strftime('%-I:%M %p').lower()}.")
                            _handover_message(request_id, "success", "Handover plan saved. Both of you can see it.")
                        st.rerun()
        elif role == "owner" and book["Exchange Type"] == "Sell" and plan.get("Paid") != "yes":
            st.button("Mark Paid", key=f"paid_{request_id}", use_container_width=True, on_click=mark_paid, args=(request_id,))
        elif role == "owner" and book["Exchange Type"] == "Lend" and plan.get("Returned") != "yes":
            st.button("Mark Returned", key=f"returned_{request_id}", use_container_width=True,
                      on_click=mark_returned, args=(request_id,))
        if done:
            rating_section(request_id, other, role)
        messages = handover.load_messages(request_id)
        with st.expander(f"Messages with {other} ({len(messages)})", expanded=False):
            for _, m in messages.iterrows():
                sent = pd.to_datetime(m["Sent At"], errors="coerce")
                st.markdown(message_html(m["Sender"], m["Text"], sent.strftime("%-d %b, %-I:%M %p").replace("AM", "am").replace("PM", "pm")
                                         if pd.notna(sent) else "", m["Sender"].lower() == user.lower()), unsafe_allow_html=True)
            with st.form(f"msg_{request_id}", clear_on_submit=True, border=False):
                text = st.text_input("Message", max_chars=handover.MAX_MESSAGE, placeholder="e.g. Can we meet at 5 pm instead?",
                                     label_visibility="collapsed")
                if st.form_submit_button("Send", use_container_width=True):
                    error = handover.check_message(text)
                    if error:
                        _handover_message(request_id, "error", error)
                    else:
                        handover.send_message(request_id, user, text)
                    st.rerun()


# ---------- Peer reviews (BS-53, story P04-US15) ----------

def reviews_section(book) -> None:
    user = st.session_state["user"]
    rows = reviews.for_title(reviews.load(), book["Title"])
    avg, count = reviews.summary(rows)
    head = (f"Reviews · ★ {avg} from {count} review{'s' if count != 1 else ''}" if count else "Reviews")
    st.markdown(f"<div style='font-size:18px;font-weight:800;margin-top:14px'>{head}</div>", unsafe_allow_html=True)
    if rows.empty:
        st.markdown(f"<div style='color:#5F6368;margin:4px 0 8px'>{reviews.MESSAGES['none']}</div>", unsafe_allow_html=True)
    for _, r in rows.iterrows():
        when = pd.to_datetime(r["Date"], errors="coerce")
        st.markdown(review_html(r["Student"], r["Stars"], r["Review"], when.strftime("%-d %b") if pd.notna(when) else r["Date"]),
                    unsafe_allow_html=True)
    mine = reviews.mine(reviews.load(), book["Title"], user)
    with st.expander("Edit your review" if mine else "Write a review", expanded=False):
        stars = st.feedback("stars", key=f"rv_stars_{book['Book ID']}")
        if mine and stars is None:
            st.caption(f"Your current rating: {int(mine['Stars'])} of 5")
        text = st.text_area(f"Your review (up to {reviews.MAX_WORDS} words) *", value=mine["Review"] if mine else "",
                            key=f"rv_text_{book['Book ID']}", height=90)
        st.caption(f"{reviews.word_count(text)} / {reviews.MAX_WORDS} words")
        if st.button("Update review" if mine else "Post review", key=f"rv_post_{book['Book ID']}", use_container_width=True):
            value = stars + 1 if stars is not None else (int(mine["Stars"]) if mine else None)
            error, message = reviews.save(book["Title"], user, value, text)
            (st.warning if error else st.success)(error or message)


def report_section(book) -> None:
    """Report a wrong listing or a student (BS-40, US09 criterion 6)."""
    user = st.session_state["user"]
    if str(book["Owner Name"]).lower() == user.lower():
        return
    with st.expander("⚑ Report this listing", expanded=False):
        reason = st.radio("Reason *", ratings.REASONS, index=None, key=f"rp_reason_{book['Book ID']}")
        details = st.text_area("Details (optional)", key=f"rp_details_{book['Book ID']}", max_chars=300, height=70)
        if st.button("Send report", key=f"rp_send_{book['Book ID']}", use_container_width=True):
            error = ratings.report(user, book["Owner Name"], book["Book ID"], book["Title"], reason, details)
            (st.warning if error else st.success)(error or ratings.MESSAGES["reported"])
        st.caption("The literary club coordinator sees every report. The other student isn't told who reported.")


# ---------- Rate my exchange partner (BS-40, story P04-US09) ----------

def rating_section(request_id: str, other: str, role: str) -> None:
    user = st.session_state["user"]
    existing = ratings.my_rating(ratings.load(), request_id, user)
    if existing:
        st.markdown(f"<div style='font-size:14px;margin:4px 0'>You rated <b>{other}</b> "
                    f"<span style='color:#B7791F;letter-spacing:1px'>{'★' * int(existing['Stars'])}{'☆' * (5 - int(existing['Stars']))}</span>"
                    f" · 🔒 one rating per exchange</div>", unsafe_allow_html=True)
        return
    st.markdown(f"<div style='font-weight:800;margin-top:6px'>How was your exchange with {other}?</div>", unsafe_allow_html=True)
    stars = st.feedback("stars", key=f"rate_{request_id}")
    if st.button("Submit rating", key=f"rate_send_{request_id}", use_container_width=True):
        error = ratings.rate(request_id, user, other, stars + 1 if stars is not None else None, True, role is not None)
        _handover_message(request_id, "error" if error else "success", error or ratings.MESSAGES["rated"])
        st.rerun()


def profile_page() -> None:
    user = st.session_state["user"]
    users, books = load_users(), load_books()
    role = users.loc[users["Name"].str.lower() == user.lower(), "Role"]
    avg, count = ratings.average(ratings.load(), user)
    listed = int((books["Owner Name"].str.lower() == user.lower()).sum())
    done = handover.load()
    exchanges = 0
    if not done.empty:
        both = done[(done["Owner Done"] == "yes") & (done["Requester Done"] == "yes")]
        requests = book_requests.load_requests()
        ids = set(both["Request ID"])
        mine = requests[requests["Request ID"].isin(ids)]
        owners = dict(zip(books["Book ID"], books["Owner Name"].str.lower()))
        exchanges = int(sum(1 for _, r in mine.iterrows()
                            if r["Requester Name"].lower() == user.lower() or owners.get(r["Book ID"]) == user.lower()))
    _, middle, _ = st.columns([1, 2, 1])
    with middle:
        st.markdown("<div style='font-size:28px;font-weight:800;letter-spacing:-0.6px;margin:10px 0 12px'>My profile</div>",
                    unsafe_allow_html=True)
        st.markdown(profile_html(user, role.iloc[0] if not role.empty else "Student", avg, count, listed, exchanges),
                    unsafe_allow_html=True)
        st.caption("Other students see your average rating on every book you list.")


# ---------- Coordinator lists: donations (BS-51) and reports (BS-40) ----------

def receive_donation(donation_id: str, book_id: str) -> None:
    error, message, changes = donations.mark_received(donation_id, announcements.is_coordinator(st.session_state["user"], load_users()))
    if not error:
        listings.update_book(book_id, changes)
    st.session_state["coord_message"] = ("error", error) if error else ("success", message)


def donations_section() -> None:
    rows = donations.coordinator_list(donations.load())
    st.markdown(section_title_html("Donations to collect", f"{len(rows)} waiting · mark Received to close the listing"),
                unsafe_allow_html=True)
    if rows.empty:
        st.caption("No donations waiting.")
    for _, d in rows.iterrows():
        offered = pd.to_datetime(d["Offered On"], errors="coerce")
        info, action = st.columns([3, 1], vertical_alignment="center")
        with info:
            st.markdown(f"<div style='background:#FFFFFF;border-radius:14px;padding:10px 14px'><b>{d['Book Title']}</b>"
                        f"<div style='font-size:13.5px;color:#5F6368'>Donated by {d['Donor']} · offered "
                        f"{offered.strftime('%-d %b %Y') if pd.notna(offered) else d['Offered On']}</div></div>",
                        unsafe_allow_html=True)
        with action:
            st.button("Received", key=f"recv_{d['Donation ID']}", use_container_width=True, on_click=receive_donation,
                      args=(d["Donation ID"], d["Book ID"]))


def reports_section() -> None:
    rows = ratings.load_reports()
    open_rows = rows[rows["Status"] == "Open"] if not rows.empty else rows
    st.markdown(section_title_html("Reports", f"{len(open_rows)} open"), unsafe_allow_html=True)
    if open_rows.empty:
        st.caption("No open reports.")
    for _, r in open_rows.iterrows():
        info, action = st.columns([3, 1], vertical_alignment="center")
        with info:
            st.markdown(f"<div style='background:#FFFFFF;border-radius:14px;padding:10px 14px'><b>{r['Reason']}</b>"
                        f"<div style='font-size:13.5px;color:#5F6368'>About {r['About Student']} · {r['About Book']} · "
                        f"reported {pd.to_datetime(r['Date']).strftime('%-d %b %Y')}</div>"
                        + (f"<div style='font-size:13.5px;margin-top:4px'>{r['Details']}</div>" if r["Details"] else "")
                        + "</div>", unsafe_allow_html=True)
        with action:
            st.button("Close", key=f"close_{r['Report ID']}", use_container_width=True, on_click=ratings.close_report,
                      args=(r["Report ID"],))


# ---------- Page flow ----------

if "user" not in st.session_state:
    sign_in_page()
else:
    if st.session_state.get("page") == "requests" and "just_requested" not in st.session_state:
        mark_requests_seen()
    top_bar()
    page = st.session_state.get("page")
    if page == "list":
        list_book_page()
    elif page == "requests":
        my_requests_page()
    elif page == "listings":
        my_listings_page()
    elif page == "wishlist":
        wishlist_page()
    elif page == "help":
        help_page()
    elif page == "coordinator":
        coordinator_page()
    elif page == "profile":
        profile_page()
    else:
        browse_page()
