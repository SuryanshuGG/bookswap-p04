"""How BookSwap looks: page styling, the top bar, book cards and covers.

Style follows Swasti's BS-24 design: mint green (#57CFA4) with black text,
light grey fields, bold black labels, rounded shapes and the Inter font.
"""

import base64
import html
import itertools
import textwrap
from pathlib import Path

import pandas as pd

MINT = "#57CFA4"        # BS-24 button colour (black text on it)
MINT_SOFT = "#E3F7EF"   # light mint for backgrounds
GREEN = "#1E6B52"       # dark mint, for text on light backgrounds
INK = "#111111"
MUTED = "#5F6368"
PAGE = "#EEF2F6"
FIELD = "#F4F4F4"
LINE = "#E3E6EA"

# Soft colour per course, used on covers that have no photo.
COURSE_TINTS = {
    "Marketing": ("#FDE7D6", "#8A3B12"),
    "Human Resources": ("#E3E8FD", "#2E3F8F"),
    "Analytics": ("#DDF4EC", "#1E6B52"),
    "Finance": ("#FFF2C7", "#7A5600"),
    "General Management": ("#EADFF7", "#5B2E8F"),
    "General Interest": ("#FBE0E6", "#8F2E45"),
}

# Status label colours on white (all pass 4.5:1 contrast).
STATUS_STYLES = {
    "Available": ("#E3F7EF", "#1E6B52"),
    "Reserved": ("#FFF1D6", "#8A5300"),
    "Exchanged": ("#ECEDEF", "#4A4F57"),
    "Paused": ("#ECEDEF", "#4A4F57"),
    "Donated": ("#E3E8FD", "#2E3F8F"),
    "Closed": ("#ECEDEF", "#4A4F57"),
}

BOOK_ICON = (
    "<svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='#111111' "
    "stroke-width='2' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'>"
    "<path d='M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3z'/><path d='M5 17a3 3 0 0 1 3-3h11'/></svg>"
)

PAGE_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, .stApp, [class*="st-"], button, input, textarea {{ font-family: 'Inter', system-ui, sans-serif !important; }}
/* Keep Streamlit's icon font for its icons (upload, close, help) */
[data-testid="stIconMaterial"], .material-symbols-rounded, [class*="material-symbols"] {{ font-family: 'Material Symbols Rounded' !important; }}
.stApp {{ background: {PAGE}; }}
/* Hide Streamlit's own toolbar, menu, footer and sidebar */
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer {{ display: none !important; }}
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}
.block-container {{ padding: 1.4rem 1.6rem 3rem; max-width: 1200px; }}

/* Buttons */
.stButton > button, .stFormSubmitButton > button {{
  border-radius: 12px; min-height: 44px; font-weight: 600; font-size: 14.5px;
  border: 1px solid {LINE}; background: #FFFFFF; color: {INK}; transition: all .15s ease;
}}
.stButton > button:hover {{ border-color: {MINT}; background: {MINT_SOFT}; color: {INK}; }}
.stFormSubmitButton > button {{ background: {MINT}; border: 0; width: 100%; font-size: 16px; min-height: 48px; }}
.stFormSubmitButton > button:hover {{ background: #45BF93; color: {INK}; }}

/* Form fields and labels */
[data-testid="stWidgetLabel"] p {{ font-weight: 700; font-size: 14.5px; color: {INK}; }}
[data-baseweb="input"], [data-baseweb="select"] > div {{ border-radius: 10px !important; background: {FIELD} !important; border-color: transparent !important; }}
[data-testid="stForm"] {{ border: 0; padding: 0; }}
/* My Listings */
[class*='st-key-mylisting_'] {{ background: #FFFFFF; border-radius: 20px; padding: 18px 18px !important; margin-bottom: 14px; }}
/* List a book page */
.st-key-listing_card {{ background: #FFFFFF; border-radius: 22px; padding: 24px 22px !important; box-shadow: 0 1px 2px rgba(17,17,17,.05); }}
.st-key-submit_listing button {{ background: {MINT} !important; border: 0 !important; min-height: 52px; font-size: 16px !important; margin-top: 8px; }}
.st-key-submit_listing button:hover {{ background: #45BF93 !important; }}
.st-key-nav_list button, .st-key-request_book button, .st-key-view_my_requests button, [class*='st-key-accept_'] button {{ background: {MINT}; border: 0; }}
.st-key-nav_list button:hover, .st-key-request_book button:hover, .st-key-view_my_requests button:hover {{ background: #45BF93; }}
[data-testid="stFileUploaderDropzone"] {{ background: {MINT_SOFT}; border: 1.5px dashed #9FD9C3; border-radius: 14px; }}
[data-testid="stButtonGroup"] button {{ border-radius: 999px !important; min-height: 42px; padding: 0 18px; }}
[data-testid="stButtonGroup"] button[aria-checked="true"], [data-testid="stButtonGroup"] button[kind*="Active"] {{ background: {MINT} !important; color: {INK} !important; border-color: {MINT} !important; }}
/* Search box on the book list */
.st-key-search [data-baseweb="input"] {{ background: #FFFFFF !important; border-radius: 14px !important; min-height: 52px; box-shadow: 0 1px 2px rgba(17,17,17,.05); }}
.st-key-search input {{ font-size: 15.5px; padding-left: 14px; }}

/* Tabs on the sign-in page: a grey pill bar with the chosen tab in white */
.stTabs [role="tablist"] {{ gap: 6px; background: #E4E9EF; padding: 5px; border-radius: 14px; border: 0 !important; box-shadow: none !important; }}
.stTabs [data-testid="stTab"] {{ flex: 1; justify-content: center; border-radius: 10px; padding: 9px 14px; color: {MUTED}; border: 0 !important; }}
.stTabs [data-testid="stTab"] p {{ font-weight: 600; font-size: 14.5px; }}
.stTabs [data-testid="stTab"][aria-selected="true"] {{ background: #FFFFFF; color: {INK}; box-shadow: 0 1px 3px rgba(17,17,17,.10); }}

/* Book cards (containers keyed card_...) become white rounded cards that lift on hover */
[class*="st-key-card_"] {{
  background: #FFFFFF; border: 0 !important; border-radius: 18px !important; padding: 12px !important;
  box-shadow: 0 1px 2px rgba(17,17,17,.05); transition: transform .15s ease, box-shadow .15s ease;
}}
[class*="st-key-card_"]:hover {{ box-shadow: 0 12px 28px rgba(17,17,17,.10); transform: translateY(-3px); }}
[class*="st-key-card_"] .stButton > button {{ background: {FIELD}; border: 0; }}
[class*="st-key-card_"] .stButton > button:hover {{ background: {MINT}; }}
/* The sign-in form sits on a white card */
.st-key-auth_card {{ background: #FFFFFF; border: 0 !important; border-radius: 22px !important; padding: 26px 24px !important; box-shadow: 0 1px 2px rgba(17,17,17,.05); }}

/* Book details pop-up */
[data-testid="stDialog"] [role="dialog"] {{ border-radius: 22px; background: #FFFFFF; }}

[class*="st-key-FormSubmitter"], [class*="st-key-FormSubmitter"] > div, [data-testid="stFormSubmitButton"], [data-testid="stFormSubmitButton"] > button {{ width: 100% !important; }}
.st-key-onboard_card [data-testid="stHorizontalBlock"], .st-key-auth_card [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; }}
.st-key-onboard_card [data-testid="stColumn"] {{ min-width: 0 !important; }}
.st-key-intro_skip {{ display: flex; justify-content: flex-end; }}
/* Welcome flow: splash, three intro steps, then a separate Sign in / Sign up page */
.st-key-splash_card {{ background: {MINT}; border-radius: 30px; padding: 40px 26px 26px !important; }}
.st-key-onboard_card, .st-key-auth_card {{ background: #FFFFFF; border-radius: 28px !important; padding: 24px 24px 22px !important; box-shadow: 0 1px 2px rgba(17,17,17,.05); }}
.st-key-get_started button {{ background: {INK} !important; color: #FFFFFF !important; border: 0 !important; min-height: 54px; font-size: 16px; }}
.st-key-get_started button:hover {{ background: #000000 !important; color: #FFFFFF !important; }}
.st-key-have_account button {{ background: rgba(255,255,255,.6) !important; border: 0 !important; min-height: 54px; font-size: 16px; }}
.st-key-intro_next button, .st-key-intro_join button {{ background: {MINT} !important; border: 0 !important; min-height: 54px; font-size: 16px; }}
.st-key-intro_next button:hover, .st-key-intro_join button:hover {{ background: #45BF93 !important; }}
.st-key-intro_skip button, .st-key-intro_back button, .st-key-auth_back button, .st-key-auth_switch button {{ background: transparent !important; border: 0 !important; color: {GREEN} !important; min-height: 36px; }}
.st-key-auth_back button, .st-key-intro_back button {{ color: {INK} !important; }}
.st-key-intro_signin button {{ background: {FIELD} !important; border: 0 !important; min-height: 54px; font-size: 16px; }}
@media (max-width: 640px) {{
  .bs-auth-panel {{ display: none !important; }}
  .st-key-splash_card {{ padding-top: 28px !important; }}
}}

@media (max-width: 640px) {{
  .bs-panel {{ min-height: 0 !important; padding: 22px 20px !important; }}
  .bs-title-inner {{ padding: 24px 22px 30px !important; }}
  .bs-title-headline {{ font-size: 30px !important; margin-top: 30px !important; }}
  .bs-panel-title {{ font-size: 24px !important; margin-top: 18px !important; }}
  .block-container {{ padding: 1rem 1rem 2.5rem; }}
}}
.bs-chip {{ display: inline-block; font-size: 12px; font-weight: 600; border-radius: 999px; padding: 4px 10px; margin: 0 4px 4px 0; white-space: nowrap; }}
</style>
"""


# ---------- Top bar and headings ----------

_LOGO_IDS = itertools.count()


def logo_svg(size: int = 38) -> str:
    """The BookSwap app icon: an open book with swap arrows on a mint tile."""
    gid = f"bsg{next(_LOGO_IDS)}"  # unique per logo, so a hidden copy never blanks the others
    return (
        f"<svg width='{size}' height='{size}' viewBox='0 0 64 64' xmlns='http://www.w3.org/2000/svg' role='img' aria-label='BookSwap logo'>"
        f"<defs><linearGradient id='{gid}' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#6EDBB3'/>"
        "<stop offset='1' stop-color='#2FB487'/></linearGradient></defs>"
        f"<rect width='64' height='64' rx='18' fill='url(#{gid})'/>"
        "<path d='M10 19.5C17 16 25 16.5 31 20.5V47C25 43.5 17 43 10 46Z' fill='#FFFFFF'/>"
        "<path d='M54 19.5C47 16 39 16.5 33 20.5V47C39 43.5 47 43 54 46Z' fill='#FFFFFF'/>"
        "<path d='M16 28.5h11.5' stroke='#1E6B52' stroke-width='2.8' stroke-linecap='round'/>"
        "<path d='M24.5 25l3.5 3.5-3.5 3.5' fill='none' stroke='#1E6B52' stroke-width='2.8' stroke-linecap='round' stroke-linejoin='round'/>"
        "<path d='M48 36.5H36.5' stroke='#111111' stroke-width='2.8' stroke-linecap='round'/>"
        "<path d='M39.5 33l-3.5 3.5 3.5 3.5' fill='none' stroke='#111111' stroke-width='2.8' stroke-linecap='round' stroke-linejoin='round'/>"
        "</svg>"
    )


def brand_html(size: int = 22, mark: str = MINT) -> str:
    return (
        f"<div style='display:flex;align-items:center;gap:10px'>{logo_svg(38)}"
        f"<span style='font-size:{size}px;font-weight:800;letter-spacing:-0.4px;color:{INK}'>BookSwap</span></div>"
    )


def user_badge_html(name: str) -> str:
    initial = html.escape(name.strip()[:1].upper() or "?")
    return (
        f"<div style='display:flex;align-items:center;justify-content:flex-end;gap:10px;height:44px'>"
        f"<span style='font-size:14px;color:{MUTED}'>Hi, <b style='color:{INK}'>{html.escape(name)}</b></span>"
        f"<span style='width:36px;height:36px;border-radius:50%;background:{MINT_SOFT};color:{GREEN};font-weight:700;"
        f"display:flex;align-items:center;justify-content:center'>{initial}</span></div>"
    )


def hero_html(total: int, counts: dict) -> str:
    chips = "".join(
        f"<span class='bs-chip' style='background:#FFFFFF;color:{INK};padding:7px 14px;font-size:13px'>"
        f"<b>{counts.get(k, 0)}</b> {k}</span>"
        for k in ("Swap", "Lend", "Sell")
    )
    return f"""
<div style="background:{MINT};border-radius:24px;padding:30px 30px 26px;margin:14px 0 22px">
  <div style="font-size:32px;font-weight:800;letter-spacing:-0.8px;color:{INK};line-height:1.15">Find your next book on campus</div>
  <div style="font-size:15.5px;color:#1F2A26;margin:8px 0 16px;max-width:560px">{total} books from XIME students. Swap, borrow or buy the books your courses need.</div>
  <div>{chips}</div>
</div>"""


def section_title_html(title: str, note: str = "") -> str:
    extra = f"<span style='font-size:14px;color:{MUTED};font-weight:500;margin-left:10px'>{html.escape(note)}</span>" if note else ""
    return f"<div style='font-size:20px;font-weight:800;color:{INK};margin:4px 0 12px'>{html.escape(title)}{extra}</div>"


def field_error_html(message: str) -> str:
    """Red message under a form field (BS-24 design)."""
    return f"<div style='color:#B42318;font-size:13.5px;font-weight:500;margin:-8px 0 10px'>{html.escape(message)}</div>"


def listed_html(book: pd.Series) -> str:
    """Success screen after listing a book (P04-US02, acceptance criteria 1, 2 and 5)."""
    tick = ("<svg width='30' height='30' viewBox='0 0 24 24' fill='none' stroke='#111111' stroke-width='2.6' "
            "stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'><path d='M5 12.5l4.5 4.5L19 7.5'/></svg>")
    return f"""
<div style="background:#FFFFFF;border-radius:24px;padding:32px 24px;text-align:center;margin-top:18px">
  <div style="width:72px;height:72px;border-radius:50%;background:{MINT};margin:0 auto 16px;display:flex;align-items:center;justify-content:center">{tick}</div>
  <div style="font-size:26px;font-weight:800;letter-spacing:-0.5px;color:{INK}">Your book is listed!</div>
  <div style="font-size:15px;color:{MUTED};margin:6px 0 20px">Other students can now find it and send you a request.</div>
  <div style="display:flex;gap:14px;text-align:left;background:{FIELD};border-radius:16px;padding:14px">
    <div style="width:84px;flex:none">{cover_html(book, max_width=84, radius=8)}</div>
    <div style="min-width:0">
      <div style="font-weight:700;font-size:16px;color:{INK}">{html.escape(str(book["Title"]))}</div>
      <div style="font-size:13.5px;color:{MUTED};margin:2px 0 8px">{html.escape(str(book["Author"]))}</div>
      <div>{exchange_chip(book)}<span class="bs-chip" style="background:#FFFFFF;color:#333333">{html.escape(str(book["Condition"]))}</span></div>
      <div style="font-size:13px;font-weight:600;color:{GREEN};margin-top:6px">● Available · Listed by {html.escape(str(book["Owner Name"]))}</div>
    </div>
  </div>
</div>"""


def empty_state_html(message: str) -> str:
    """Shown when a search finds no books (P04-US03, acceptance criterion 2)."""
    return (
        f"<div style='background:#FFFFFF;border-radius:18px;padding:36px 24px;text-align:center'>"
        f"<div style='width:56px;height:56px;border-radius:16px;background:{MINT_SOFT};margin:0 auto 14px;"
        f"display:flex;align-items:center;justify-content:center'>{BOOK_ICON}</div>"
        f"<div style='font-size:16px;font-weight:700;color:{INK};max-width:420px;margin:0 auto'>{html.escape(message)}</div></div>"
    )


# ---------- Covers ----------

def _placeholder_svg(book: pd.Series) -> str:
    """A typographic cover with the title, shown when there is no photo or the
    photo link is broken (US01, acceptance criterion 4)."""
    bg, fg = COURSE_TINTS.get(str(book.get("Course")), (MINT_SOFT, GREEN))
    lines = textwrap.wrap(str(book.get("Title", "")), width=13)[:4]
    title = "".join(
        f"<text x='28' y='{120 + i * 36}' font-family='Inter,Arial,sans-serif' font-size='29' font-weight='800' fill='{fg}'>{html.escape(t)}</text>"
        for i, t in enumerate(lines)
    )
    author = html.escape(textwrap.shorten(str(book.get("Author", "")), width=24, placeholder="…"))
    return (
        "<svg xmlns='http://www.w3.org/2000/svg' width='300' height='450' viewBox='0 0 300 450'>"
        f"<rect width='300' height='450' fill='{bg}'/>"
        f"<rect x='28' y='52' width='44' height='6' rx='3' fill='{fg}' opacity='0.5'/>"
        f"{title}"
        f"<text x='28' y='392' font-family='Inter,Arial,sans-serif' font-size='17' font-weight='600' fill='{fg}'>{author}</text>"
        f"<text x='28' y='418' font-family='Inter,Arial,sans-serif' font-size='13' fill='{fg}' opacity='0.75'>No cover photo</text>"
        "</svg>"
    )


def cover_html(book: pd.Series, max_width: int = 400, radius: int = 14) -> str:
    """Book-shaped cover. The title cover sits underneath the real photo, so a
    missing or broken photo link shows the title cover instead of a broken image."""
    placeholder = "data:image/svg+xml;base64," + base64.b64encode(_placeholder_svg(book).encode()).decode()
    link = str(book.get("Cover Image Link") or "").strip()
    layers, sizes = f"url('{placeholder}')", "cover"
    # A web link, or a photo a student uploaded when listing the book (BS-25)
    if link.lower().startswith(("http://", "https://", "data:image/jpeg;base64,", "data:image/png;base64,")):
        layers = f"url('{html.escape(link, quote=True)}'), {layers}"
        sizes = "cover, cover"
    return (
        f"<div style=\"width:100%;max-width:{max_width}px;aspect-ratio:2/3;margin:0 auto;border-radius:{radius}px;"
        f"background-color:#F4F4F4;background-image:{layers};background-size:{sizes};"
        f"background-position:center;background-repeat:no-repeat;\"></div>"
    )


# ---------- Labels ----------

def price_text(book: pd.Series) -> str:
    """Price in rupees for Sell books; Lend and Swap have no price."""
    price = book.get("Price (Rs)")
    if book.get("Exchange Type") == "Sell" and pd.notna(price):
        return f"₹{int(price):,}"
    return "—"


def exchange_chip(book: pd.Series) -> str:
    kind = str(book["Exchange Type"])
    if kind == "Sell":
        return f"<span class='bs-chip' style='background:{MINT};color:{INK}'>Sell · {price_text(book)}</span>"
    return f"<span class='bs-chip' style='background:{MINT_SOFT};color:{GREEN}'>{html.escape(kind)}</span>"


def status_chip(status: str) -> str:
    bg, fg = STATUS_STYLES.get(status, STATUS_STYLES["Available"])
    return f"<span class='bs-chip' style='background:{bg};color:{fg}'>● {html.escape(status)}</span>"


# ---------- Book card and details ----------

def card_html(book: pd.Series) -> str:
    """One book card: cover, title, author, condition, exchange type and status."""
    return f"""
<div>
  {cover_html(book)}
  <div style="font-weight:700;font-size:15px;color:{INK};margin-top:12px;line-height:1.3;height:2.6em;overflow:hidden;">{html.escape(str(book["Title"]))}</div>
  <div style="color:{MUTED};font-size:13px;margin:3px 0 10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{html.escape(str(book["Author"]))}</div>
  <div>{exchange_chip(book)}<span class="bs-chip" style="background:{FIELD};color:#333333">{html.escape(str(book["Condition"]))}</span></div>
  <div>{status_chip(str(book["Status"]))}</div>
</div>"""


def details_html(book: pd.Series) -> str:
    """Everything about one book (US01, acceptance criterion 3)."""
    rows = [
        ("Course", book["Course"]),
        ("Genre", book["Genre"]),
        ("Condition", book["Condition"]),
        ("Exchange type", book["Exchange Type"]),
        ("Price", price_text(book)),
        ("Book ID", book["Book ID"]),
    ]
    cells = "".join(
        f"<div style='background:{FIELD};border-radius:12px;padding:10px 12px'>"
        f"<div style='font-size:12px;color:{MUTED};font-weight:600'>{html.escape(label)}</div>"
        f"<div style='font-size:15px;color:{INK};font-weight:700;margin-top:2px'>{html.escape(str(value))}</div></div>"
        for label, value in rows
    )
    owner = html.escape(str(book["Owner Name"]))
    return f"""
<div style="font-size:24px;font-weight:800;color:{INK};line-height:1.2;letter-spacing:-0.4px">{html.escape(str(book['Title']))}</div>
<div style="font-size:15px;color:{MUTED};margin:6px 0 12px">by {html.escape(str(book['Author']))}</div>
<div style="margin-bottom:14px">{exchange_chip(book)}{status_chip(str(book['Status']))}</div>
<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px">{cells}</div>
<div style="display:flex;align-items:center;gap:10px;margin-top:16px;padding-top:14px;border-top:1px solid {LINE}">
  <span style="width:36px;height:36px;border-radius:50%;background:{MINT_SOFT};color:{GREEN};font-weight:700;display:flex;align-items:center;justify-content:center">{html.escape(owner[:1].upper())}</span>
  <span style="font-size:14px;color:{MUTED}">Listed by <b style="color:{INK}">{owner}</b></span>
</div>"""


# ---------- Sign-in page side panel ----------

def welcome_panel_html(total: int) -> str:
    points = [
        ("Swap", "Trade a book you've finished for one you need."),
        ("Lend", "Borrow for a term and give it back."),
        ("Sell", "Buy second-hand at student prices."),
    ]
    items = "".join(
        f"<div style='display:flex;gap:12px;align-items:flex-start;margin-top:14px'>"
        f"<span style='flex:none;background:#FFFFFF;border-radius:10px;padding:5px 10px;font-size:13px;font-weight:700;color:{INK}'>{k}</span>"
        f"<span style='font-size:15px;color:#1F2A26;line-height:1.45'>{v}</span></div>"
        for k, v in points
    )
    return f"""
<div class="bs-panel" style="background:{MINT};border-radius:26px;padding:34px 30px;min-height:430px;box-sizing:border-box">
  {brand_html(24, mark='#FFFFFF')}
  <div class="bs-panel-title" style="font-size:34px;font-weight:800;letter-spacing:-0.9px;line-height:1.12;color:{INK};margin-top:34px">Books for every course, from students on campus.</div>
  {items}
  <div style="margin-top:28px;font-size:14px;font-weight:600;color:#1F2A26">{total} books listed right now</div>
</div>"""


# ---------- Requests (BS-31, story P04-US05; layout from Swasti's BS-32 design) ----------

REQUEST_STATUS_STYLES = {
    "Pending": ("#FFF1D6", "#8A5300"),
    "Accepted": ("#E3F7EF", "#1E6B52"),
    "Declined": ("#FDE8E8", "#B42318"),
}


def request_status_chip(status: str) -> str:
    bg, fg = REQUEST_STATUS_STYLES.get(status, REQUEST_STATUS_STYLES["Pending"])
    return f"<span class='bs-chip' style='background:{bg};color:{fg}'>● {html.escape(status)}</span>"


def request_label_html(label: str, message: str, mint: bool = False) -> str:
    """BS-32 states B, C and D: a label in place of the Request button, with the reason."""
    bg, fg = (MINT_SOFT, GREEN) if mint else (FIELD, MUTED)
    return (
        f"<div style='background:{bg};color:{fg};border-radius:12px;text-align:center;padding:12px 0;"
        f"font-size:15px;font-weight:700;margin-top:14px'>{html.escape(label)}</div>"
        f"<div style='font-size:13.5px;color:{MUTED};text-align:center;margin-top:8px'>{html.escape(message)}</div>"
    )


def note_html(text: str) -> str:
    """A short note box, e.g. the pay-at-handover line for Sell books."""
    return (
        f"<div style='background:{MINT_SOFT};color:{GREEN};border-radius:12px;padding:10px 12px;"
        f"font-size:13.5px;font-weight:600;margin-top:12px'>{html.escape(text)}</div>"
    )


def request_sent_html(book: pd.Series, owner: str, extra: str = "") -> str:
    """BS-32 screen 2: Request sent!"""
    tick = ("<svg width='30' height='30' viewBox='0 0 24 24' fill='none' stroke='#111111' stroke-width='2.6' "
            "stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'><path d='M5 12.5l4.5 4.5L19 7.5'/></svg>")
    extra_html = f"<div style='font-size:13px;color:{GREEN};font-weight:600;margin-top:6px'>{html.escape(extra)}</div>" if extra else ""
    return f"""
<div style="background:#FFFFFF;border-radius:24px;padding:32px 24px;text-align:center;margin-top:18px">
  <div style="width:72px;height:72px;border-radius:50%;background:{MINT};margin:0 auto 16px;display:flex;align-items:center;justify-content:center">{tick}</div>
  <div style="font-size:26px;font-weight:800;letter-spacing:-0.5px;color:{INK}">Request sent!</div>
  <div style="font-size:15px;color:{MUTED};margin:6px 0 20px;line-height:1.5">{html.escape(owner)} will see your request for<br><b style="color:{INK}">{html.escape(str(book["Title"]))}</b>. You'll find it in My Requests.</div>
  <div style="display:flex;gap:14px;text-align:left;background:{FIELD};border-radius:16px;padding:14px;align-items:center">
    <div style="width:64px;flex:none">{cover_html(book, max_width=64, radius=7)}</div>
    <div style="min-width:0">
      <div style="font-weight:700;font-size:16px;color:{INK}">{html.escape(str(book["Title"]))}</div>
      <div style="font-size:13px;color:{MUTED};margin:2px 0 8px">Requested today</div>
      <div>{request_status_chip("Pending")}</div>
      {extra_html}
    </div>
  </div>
</div>"""


def request_row_html(row: pd.Series, extra: str = "") -> str:
    """One row in My Requests (BS-32 screen 3)."""
    when = pd.to_datetime(row["Request Date"], errors="coerce")
    when_text = when.strftime("%-d %b") if pd.notna(when) else str(row["Request Date"])
    note = ""
    if row["Status"] == "Accepted":
        note = f"Collect it from {row['Owner Name']}."
    extra_html = "".join(
        f"<div style='font-size:12.5px;color:{GREEN};font-weight:600;margin-top:4px'>{html.escape(t)}</div>"
        for t in (extra, note) if t
    )
    return f"""
<div style="display:flex;gap:14px;align-items:center;background:#FFFFFF;border-radius:16px;padding:12px 14px;margin-bottom:10px">
  <div style="width:52px;flex:none">{cover_html(row, max_width=52, radius=7)}</div>
  <div style="min-width:0;flex:1">
    <div style="font-weight:700;font-size:15.5px;color:{INK}">{html.escape(str(row["Title"]))}</div>
    <div style="font-size:12.5px;color:{MUTED};margin:2px 0 6px">Owner: {html.escape(str(row["Owner Name"]))} · {html.escape(str(row["Exchange Type"]))} · {when_text}</div>
    <div>{request_status_chip(str(row["Status"]))}</div>
    {extra_html}
  </div>
</div>"""



# ---------- My Listings (BS-36 and BS-56, story P04-US07) ----------

def listing_header_html(book: pd.Series, pending: int) -> str:
    """One of my books on My Listings: cover, title, labels and how many requests wait."""
    waiting = (f"<span class='bs-chip' style='background:#FFF1D6;color:#8A5300'>{pending} new request{'s' if pending != 1 else ''}</span>"
               if pending else "")
    return f"""
<div style="display:flex;gap:14px;align-items:center">
  <div style="width:58px;flex:none">{cover_html(book, max_width=58, radius=8)}</div>
  <div style="min-width:0">
    <div style="font-weight:800;font-size:16.5px;color:{INK}">{html.escape(str(book["Title"]))}</div>
    <div style="font-size:13px;color:{MUTED};margin:2px 0 8px">{html.escape(str(book["Author"]))} · {html.escape(str(book["Condition"]))}</div>
    <div>{exchange_chip(book)}{status_chip(str(book["Status"]))}{waiting}</div>
  </div>
</div>"""


def owner_request_html(row: pd.Series, extra: str = "") -> str:
    """A request on one of my books, as the owner sees it."""
    when = pd.to_datetime(row["Request Date"], errors="coerce")
    when_text = when.strftime("%-d %b") if pd.notna(when) else str(row["Request Date"])
    initial = html.escape(str(row["Requester Name"])[:1].upper())
    extra_html = f"<div style='font-size:13px;color:{GREEN};font-weight:600;margin-top:4px'>{html.escape(extra)}</div>" if extra else ""
    return f"""
<div style="display:flex;gap:12px;align-items:center;background:{FIELD};border-radius:14px;padding:10px 12px;margin-top:10px">
  <span style="width:34px;height:34px;flex:none;border-radius:50%;background:{MINT_SOFT};color:{GREEN};font-weight:700;display:flex;align-items:center;justify-content:center">{initial}</span>
  <div style="min-width:0;flex:1">
    <div style="font-size:14.5px;color:{INK}"><b>{html.escape(str(row["Requester Name"]))}</b> requested this book · {when_text}</div>
    <div style="margin-top:4px">{request_status_chip(str(row["Status"]))}</div>
    {extra_html}
  </div>
</div>"""


# ---------- Title page (sign-in page hero) ----------

HERO_PHOTO = Path(__file__).resolve().parent.parent / "assets" / "hero_books.jpg"
HERO_CREDIT = ("Photo: Tom Hermans on Unsplash", "https://unsplash.com/photos/book-lot-on-table-9BoqXzEeQqM")


def _hero_photo_uri() -> str:
    try:
        return "data:image/jpeg;base64," + base64.b64encode(HERO_PHOTO.read_bytes()).decode()
    except OSError:
        return ""


def title_hero_html(total: int, counts: dict) -> str:
    """Full-width title banner with a book photo, shown above Welcome / Sign in."""
    photo = _hero_photo_uri()
    background = (f"linear-gradient(90deg, rgba(17,17,17,.82) 0%, rgba(17,17,17,.62) 45%, rgba(17,17,17,.15) 100%), url('{photo}')"
                  if photo else f"linear-gradient(90deg, {GREEN}, {MINT})")
    chips = "".join(
        f"<span class='bs-chip' style='background:{MINT};color:{INK};padding:7px 14px;font-size:13.5px'>"
        f"<b>{counts.get(k, 0)}</b>&nbsp;{k}</span>"
        for k in ("Swap", "Lend", "Sell")
    )
    credit, credit_link = HERO_CREDIT
    return f"""
<div class="bs-title-hero" style="position:relative;border-radius:28px;overflow:hidden;margin:6px 0 26px;
     background:{background};background-size:cover;background-position:center 60%;">
  <div class="bs-title-inner" style="padding:34px 40px 40px;max-width:640px">
    {brand_html(24, mark='#FFFFFF').replace(f'color:{INK}', 'color:#FFFFFF')}
    <div class="bs-title-headline" style="font-size:46px;font-weight:800;letter-spacing:-1.4px;line-height:1.06;color:#FFFFFF;margin-top:54px">
      Books for every course, from students on campus.</div>
    <div style="font-size:17px;color:#E9EEEC;margin:14px 0 22px;line-height:1.5;max-width:520px">
      Swap a book you've finished, borrow one for the term, or buy second-hand at student prices.</div>
    <div>{chips}</div>
    <div style="margin-top:26px;display:flex;gap:12px;flex-wrap:wrap;align-items:center">
      <a href="#welcome" target="_self" style="background:#FFFFFF;color:{INK};text-decoration:none;font-weight:700;font-size:15px;
         padding:12px 22px;border-radius:12px">Sign in or join ↓</a>
      <span style="color:#E9EEEC;font-size:14px;font-weight:600">{total} books listed right now</span>
    </div>
  </div>
  <a href="{credit_link}" target="_blank" rel="noopener" style="position:absolute;right:16px;bottom:12px;font-size:11.5px;
     color:rgba(255,255,255,.8);text-decoration:none">{html.escape(credit)}</a>
</div>"""


# ---------- Welcome flow (BS-5): splash, intro steps, then Sign in / Sign up ----------

def splash_html() -> str:
    """First screen: only the app icon, name and one line. No book counts."""
    return f"""
<div style="display:flex;flex-direction:column;align-items:center;text-align:center;padding:36px 0 34px">
  <div style="border-radius:30px;box-shadow:0 18px 40px rgba(17,17,17,.16);line-height:0">{logo_svg(104)}</div>
  <div style="font-size:40px;font-weight:800;letter-spacing:-1.2px;color:{INK};margin-top:22px">BookSwap</div>
  <div style="font-size:16px;font-weight:500;color:#1F2A26;line-height:1.45;max-width:280px;margin-top:8px">
    Swap, borrow and buy books from students on your campus.</div>
</div>"""


def _dots(step: int) -> str:
    return "".join(
        f"<span style='display:inline-block;height:8px;border-radius:4px;margin-right:6px;"
        f"width:{26 if i == step else 8}px;background:{INK if i == step else '#D5DADF'}'></span>"
        for i in range(3)
    )


def _row(icon_bg: str, title: str, sub: str) -> str:
    return (f"<div style='background:#FFFFFF;border-radius:18px;padding:13px 15px;display:flex;align-items:center;gap:12px;margin-top:10px'>"
            f"<span style='flex:none;width:40px;height:40px;border-radius:13px;background:{icon_bg}'></span>"
            f"<div style='text-align:left'><div style='font-size:15px;font-weight:700;color:{INK}'>{title}</div>"
            f"<div style='font-size:13px;color:{MUTED}'>{sub}</div></div></div>")


INTRO_STEPS = [
    ("Give your old books a second semester",
     "Swap a book you've finished, lend it for a term, or sell it at a student price."),
    ("Request any book in one tap",
     "Offer one of your books for a swap. For books on sale, pay the owner at handover by UPI or cash."),
    ("Meet on campus, hand it over",
     "Pick a spot and time on campus. Only XIME students can join."),
]


def onboarding_html(step: int) -> str:
    title, body = INTRO_STEPS[step]
    if step == 0:
        photo = _hero_photo_uri()
        pills = "".join(
            f"<span style='flex:1;text-align:center;background:{MINT if k == 'Sell' else '#FFFFFF'};border-radius:14px;padding:10px 0;font-size:14px;font-weight:700;color:{INK}'>{k}</span>"
            for k in ("Swap", "Lend", "Sell"))
        visual = (f"<div style=\"height:300px;border-radius:24px;position:relative;overflow:hidden;background:{MINT_SOFT} url('{photo}') center/cover\">"
                  f"<div style='position:absolute;left:14px;right:14px;bottom:14px;display:flex;gap:8px'>{pills}</div></div>")
    elif step == 1:
        visual = (f"<div style='height:300px;border-radius:24px;background:{MINT_SOFT};display:flex;flex-direction:column;justify-content:center;padding:0 20px;box-sizing:border-box'>"
                  f"<div style='background:#FFFFFF;border-radius:18px;padding:16px;text-align:left;box-shadow:0 10px 28px rgba(30,107,82,.14)'>"
                  f"<div style='font-size:16px;font-weight:800;color:{INK}'>Atomic Habits</div>"
                  f"<div style='font-size:13px;color:{MUTED};margin:2px 0 8px'>James Clear · Like New</div>"
                  f"<span class='bs-chip' style='background:{MINT_SOFT};color:{GREEN}'>Swap</span>"
                  f"<div style='font-size:13px;color:{GREEN};font-weight:600;margin-top:4px'>You offer: Corporate Finance</div></div>"
                  f"<div style='background:{INK};color:#FFFFFF;border-radius:14px;height:48px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px;margin-top:12px'>✓ Request sent · Pending</div></div>")
    else:
        visual = (f"<div style='height:300px;border-radius:24px;background:{MINT_SOFT};display:flex;flex-direction:column;justify-content:center;padding:0 20px 10px;box-sizing:border-box'>"
                  + _row(MINT, "Library entrance", "Thu · 4:30 pm")
                  + _row("#FFF1D6", "Return by the date set", "For books you borrow")
                  + _row("#E3E8FD", "Pay at handover", "UPI or cash, for books on sale") + "</div>")
    return f"""
<div style="font-size:13px;font-weight:600;color:{MUTED};text-align:center;margin-bottom:12px">{step + 1} of 3</div>
{visual}
<div style="font-size:29px;font-weight:800;letter-spacing:-0.9px;line-height:1.12;color:{INK};margin-top:24px">{title}</div>
<div style="font-size:16px;color:{MUTED};line-height:1.5;margin:10px 0 18px">{body}</div>
<div style="margin-bottom:14px">{_dots(step)}</div>"""


def auth_heading_html(mode: str) -> str:
    """The Welcome heading on the separate Sign in / Sign up page."""
    if mode == "signup":
        title, sub = "Welcome to BookSwap", "Create your account with your XIME email."
    else:
        title, sub = "Welcome back", "Sign in with your XIME email."
    return (f"<div style='margin:4px 0 18px'>{logo_svg(48)}"
            f"<div style='font-size:32px;font-weight:800;letter-spacing:-0.9px;color:{INK};margin-top:16px'>{title}</div>"
            f"<div style='font-size:15.5px;color:{MUTED};margin-top:4px'>{sub}</div></div>")


def auth_panel_html() -> str:
    """Left panel on desktop beside the Sign in form (hidden on phones). No book counts."""
    points = ["Swap, lend or sell to classmates", "Request in one tap, pay at handover", "Meet on campus. XIME students only"]
    items = "".join(
        f"<div style='display:flex;gap:12px;align-items:center;margin-top:14px'>"
        f"<span style='flex:none;width:30px;height:30px;border-radius:15px;background:rgba(255,255,255,.7);display:flex;align-items:center;justify-content:center;font-weight:800;color:{INK}'>✓</span>"
        f"<span style='font-size:15.5px;font-weight:600;color:{INK}'>{p}</span></div>" for p in points)
    return f"""
<div class="bs-auth-panel" style="background:{MINT};border-radius:28px;padding:34px 34px;min-height:520px;box-sizing:border-box;display:flex;flex-direction:column">
  {brand_html(24)}
  <div style="flex:1"></div>
  <div style="font-size:36px;font-weight:800;letter-spacing:-1px;line-height:1.1;color:{INK}">Give your old books a second semester</div>
  {items}
</div>"""


# ---------- Help page (P04-US11) ----------

def help_page_html(guidelines, how_to, points, hours: str) -> str:
    """Guidelines, five-step how-to and approved handover points on one page."""
    steps = "".join(
        f"<div style='display:flex;gap:14px;align-items:flex-start;margin-top:12px'>"
        f"<span style='flex:none;width:30px;height:30px;border-radius:15px;background:{MINT};color:{INK};"
        f"font-weight:800;display:flex;align-items:center;justify-content:center'>{n}</span>"
        f"<div><div style='font-weight:700;color:{INK}'>{html.escape(title)}</div>"
        f"<div style='color:{MUTED};font-size:14.5px;line-height:1.45'>{html.escape(text)}</div></div></div>"
        for n, (title, text) in enumerate(how_to, start=1))
    place_rows = "".join(
        f"<div style='display:flex;gap:12px;align-items:center;background:{FIELD};border-radius:14px;padding:10px 12px;margin-top:8px'>"
        f"<span style='flex:none;width:34px;height:34px;border-radius:11px;background:{MINT_SOFT};display:flex;align-items:center;justify-content:center'>"
        f"<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='{GREEN}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'>"
        f"<path d='M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z'/><circle cx='12' cy='9.5' r='2.5'/></svg></span>"
        f"<div><div style='font-weight:700;color:{INK}'>{html.escape(name)}</div>"
        f"<div style='font-size:13px;color:{MUTED}'>{html.escape(where)}</div></div></div>"
        for name, where in points)
    sections = "".join(
        f"<div style='background:#FFFFFF;border-radius:20px;padding:20px 22px;margin-top:14px'>"
        f"<div style='font-size:18px;font-weight:800;color:{INK}'>{html.escape(title)}</div>"
        f"<ul style='margin:10px 0 0 0;padding-left:20px;color:#333333;font-size:14.5px;line-height:1.55'>"
        + "".join(f"<li style='margin-top:4px'>{html.escape(rule)}</li>" for rule in rules)
        + "</ul>"
        + (f"<div style='font-weight:700;color:{INK};margin-top:14px'>Approved handover points · {html.escape(hours)}</div>{place_rows}"
           if title == "Safe meeting" else "")
        + "</div>"
        for title, rules in guidelines)
    return f"""
<div style="font-size:28px;font-weight:800;letter-spacing:-0.6px;color:{INK};margin:10px 0 4px">Help</div>
<div style="color:{MUTED};font-size:15px">How BookSwap works, and the rules every member agrees to.</div>
<div style="background:#FFFFFF;border-radius:20px;padding:20px 22px;margin-top:16px">
  <div style="font-size:18px;font-weight:800;color:{INK}">How to list and request a book</div>
  {steps}
</div>
{sections}
<div style="font-size:12.5px;color:{MUTED};margin:14px 4px 0">Guidelines approved by the literary club coordinator.</div>"""


# ---------- Wishlist (P04-US10) ----------

def wish_row_html(title: str, author: str, added: str, available: bool, match_count: int = 0) -> str:
    """One wishlist entry with its Now Available or Waiting chip."""
    if available:
        chip = (f"<span class='bs-chip' style='background:{MINT};color:{INK}'>● Now Available</span>"
                f"<span style='font-size:13px;color:{GREEN};font-weight:600;margin-left:6px'>"
                f"{match_count} cop{'y' if match_count == 1 else 'ies'} listed</span>")
    else:
        chip = f"<span class='bs-chip' style='background:{FIELD};color:#333333'>Waiting for a listing</span>"
    by = f" · {html.escape(author)}" if author else ""
    return (
        f"<div style='background:#FFFFFF;border-radius:18px;padding:16px 18px;margin-top:4px;"
        f"{'border:2px solid ' + MINT + ';' if available else ''}'>"
        f"<div style='font-weight:800;font-size:16px;color:{INK}'>{html.escape(title)}</div>"
        f"<div style='font-size:13.5px;color:{MUTED};margin:2px 0 10px'>Saved {html.escape(added)}{by}</div>"
        f"<div>{chip}</div></div>"
    )


# ---------- Reading circle announcements (P04-US13) ----------

def announcements_html(items: list[dict]) -> str:
    """Cards on the home screen, soonest first. items: title, date_text, time_text, venue, details."""
    if not items:
        return ""
    cards = "".join(
        f"<div style='flex:1 1 260px;background:#FFFFFF;border-radius:18px;padding:14px 16px;border-left:5px solid {MINT}'>"
        f"<div style='font-size:12px;font-weight:700;color:{GREEN};letter-spacing:.3px'>READING CIRCLE · {html.escape(a['date_text'])}</div>"
        f"<div style='font-size:16.5px;font-weight:800;color:{INK};margin-top:4px'>{html.escape(a['title'])}</div>"
        f"<div style='font-size:13.5px;color:{MUTED};margin-top:2px'>{html.escape(a['time_text'])} · {html.escape(a['venue'])}</div>"
        + (f"<div style='font-size:13.5px;color:#333333;margin-top:6px'>{html.escape(a['details'])}</div>" if a.get("details") else "")
        + "</div>"
        for a in items)
    return f"<div style='display:flex;flex-wrap:wrap;gap:12px;margin:4px 0 14px'>{cards}</div>"


# ---------- Handover (P04-US08) ----------

def handover_card_html(plan_text: str, where: str, proposer: str, steps: list[tuple[str, bool]],
                       outcome: str = "", outcome_tone: str = "good") -> str:
    """The agreed point and time, who has confirmed, and the result. steps: (label, done)."""
    tones = {"good": (MINT_SOFT, GREEN), "warn": ("#FFF1D6", "#8A5300"), "bad": ("#FDE7E7", "#B42318")}
    bg, fg = tones.get(outcome_tone, tones["good"])
    plan = (f"<div style='font-weight:800;font-size:15.5px;color:{INK}'>📍 {html.escape(plan_text)}</div>"
            f"<div style='font-size:13px;color:{MUTED};margin-top:2px'>{html.escape(where)}"
            f"{' · proposed by ' + html.escape(proposer) if proposer else ''}</div>") if plan_text else (
            f"<div style='font-weight:700;color:{INK}'>No handover planned yet</div>"
            f"<div style='font-size:13px;color:{MUTED};margin-top:2px'>Choose an approved campus point and a time below.</div>")
    ticks = "".join(
        f"<span style='display:inline-block;margin:8px 8px 0 0;font-size:13px;font-weight:600;border-radius:999px;padding:4px 10px;"
        f"background:{MINT if done else FIELD};color:{INK}'>{'✓' if done else '○'} {html.escape(label)}</span>"
        for label, done in steps)
    result = (f"<div style='margin-top:10px;background:{bg};color:{fg};border-radius:12px;padding:8px 12px;"
              f"font-weight:700;font-size:14px'>{html.escape(outcome)}</div>") if outcome else ""
    return (f"<div style='background:#FFFFFF;border:1.5px solid {MINT};border-radius:16px;padding:14px 16px;margin:6px 0'>"
            f"<div style='font-size:12px;font-weight:800;letter-spacing:.4px;color:{GREEN};margin-bottom:6px'>HANDOVER</div>"
            f"{plan}{ticks}{result}</div>")


def message_html(sender: str, text: str, when: str, mine: bool) -> str:
    side = "flex-end" if mine else "flex-start"
    bg = MINT_SOFT if mine else FIELD
    return (f"<div style='display:flex;justify-content:{side};margin:4px 0'><div style='max-width:80%;background:{bg};"
            f"border-radius:14px;padding:8px 12px'><div style='font-size:12px;color:{MUTED}'>{html.escape(sender)} · "
            f"{html.escape(when)}</div><div style='font-size:14.5px;color:{INK}'>{html.escape(text)}</div></div></div>")


# ---------- Ratings and reviews (P04-US09, P04-US15) ----------

def stars_text(value) -> str:
    """'★★★★☆' for 4 (rounded)."""
    n = int(round(float(value))) if value not in (None, "") else 0
    return "★" * n + "☆" * (5 - n)


def rating_line_html(name: str, avg, count: int, label: str = "Listed by") -> str:
    """Criteria 2 and 5 of P04-US09: average rating, or No ratings yet."""
    score = (f"<span style='color:#B7791F;letter-spacing:1px'>{stars_text(avg)}</span> "
             f"<b>{avg}</b> <span style='color:{MUTED}'>({count} rating{'s' if count != 1 else ''})</span>") if count else (
             f"<span style='color:{MUTED}'>No ratings yet</span>")
    return (f"<div style='font-size:14px;margin:10px 0 2px;color:{INK}'>"
            f"<b>{html.escape(name)}</b>'s exchange rating · {score}</div>")


def review_html(student: str, stars, text: str, when: str) -> str:
    return (f"<div style='border-top:1px solid #E3E6EA;padding:10px 0'>"
            f"<div style='font-size:13.5px'><b>{html.escape(student)}</b> "
            f"<span style='color:#B7791F;letter-spacing:1px'>{stars_text(stars)}</span> "
            f"<span style='color:{MUTED}'>· {html.escape(when)}</span></div>"
            f"<div style='font-size:14.5px;color:#333333;margin-top:2px'>{html.escape(text)}</div></div>")


def profile_html(name: str, role: str, avg, count: int, listed: int, exchanges: int) -> str:
    score = (f"<div style='font-size:40px;font-weight:800;letter-spacing:-1px'>{avg}</div>"
             f"<div><div style='color:#B7791F;font-size:20px;letter-spacing:2px'>{stars_text(avg)}</div>"
             f"<div style='color:{MUTED};font-size:13.5px'>from {count} rating{'s' if count != 1 else ''}</div></div>") if count else (
             f"<div style='color:{MUTED};font-size:16px;font-weight:600'>No ratings yet</div>")
    stat = lambda n, label: (f"<div style='flex:1;background:{FIELD};border-radius:14px;padding:10px;text-align:center'>"
                             f"<div style='font-size:20px;font-weight:800'>{n}</div><div style='font-size:12.5px;color:{MUTED}'>{label}</div></div>")
    return (f"<div style='background:#FFFFFF;border-radius:20px;padding:22px;text-align:center'>"
            f"<div style='width:62px;height:62px;border-radius:31px;background:{MINT_SOFT};color:{GREEN};font-weight:800;font-size:24px;"
            f"display:flex;align-items:center;justify-content:center;margin:0 auto 8px'>{html.escape(name[:1].upper())}</div>"
            f"<div style='font-size:21px;font-weight:800'>{html.escape(name)}</div>"
            f"<div style='color:{MUTED};font-size:13.5px'>{html.escape(role)} · XIME Bangalore</div>"
            f"<div style='display:flex;gap:12px;align-items:center;justify-content:center;margin-top:12px'>{score}</div>"
            f"<div style='display:flex;gap:10px;margin-top:16px'>{stat(listed, 'books listed')}{stat(exchanges, 'exchanges')}</div></div>")
