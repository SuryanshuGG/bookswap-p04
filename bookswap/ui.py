"""How BookSwap looks: page styling, the top bar, book cards and covers.

Style follows Swasti's BS-24 design: mint green (#57CFA4) with black text,
light grey fields, bold black labels, rounded shapes and the Inter font.
"""

import base64
import html
import textwrap

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

@media (max-width: 640px) {{
  .bs-panel {{ min-height: 0 !important; padding: 22px 20px !important; }}
  .bs-panel-title {{ font-size: 24px !important; margin-top: 18px !important; }}
  .block-container {{ padding: 1rem 1rem 2.5rem; }}
}}
.bs-chip {{ display: inline-block; font-size: 12px; font-weight: 600; border-radius: 999px; padding: 4px 10px; margin: 0 4px 4px 0; white-space: nowrap; }}
</style>
"""


# ---------- Top bar and headings ----------

def brand_html(size: int = 22, mark: str = MINT) -> str:
    return (
        f"<div style='display:flex;align-items:center;gap:10px'>"
        f"<div style='width:38px;height:38px;border-radius:11px;background:{mark};display:flex;align-items:center;justify-content:center'>{BOOK_ICON}</div>"
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
    if link.lower().startswith(("http://", "https://")):
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
