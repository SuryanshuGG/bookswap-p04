"""Page styling and small pieces of layout: the book card and the cover image.

Colours and font follow Swasti's BS-24 design: mint green (#57CFA4), light grey
fields, bold black labels, rounded pill buttons and the Inter font.
"""

import base64
import html

import pandas as pd

GREEN = "#1E6B52"  # dark mint, for text on light backgrounds
MINT = "#57CFA4"  # BS-24 button colour (black text on it)
INK = "#111111"
MUTED = "#5F6368"
PAPER = "#E9EEF3"
LINE = "#E3E6EA"

# Shown when a book has no cover link, or when its link stops working
# (US01, acceptance criterion 4).
_PLACEHOLDER_SVG = """<svg xmlns='http://www.w3.org/2000/svg' width='300' height='450' viewBox='0 0 300 450'>
<rect width='300' height='450' fill='#E3F7EF'/>
<path d='M95 140h95a25 25 0 0 1 25 25v150H120a25 25 0 0 1-25-25z' fill='none' stroke='#57CFA4' stroke-width='9' stroke-linejoin='round'/>
<path d='M95 290a25 25 0 0 1 25-25h95' fill='none' stroke='#57CFA4' stroke-width='9'/>
<text x='150' y='375' font-family='sans-serif' font-size='24' font-weight='600' fill='#1E6B52' text-anchor='middle'>No cover</text>
</svg>"""
PLACEHOLDER = "data:image/svg+xml;base64," + base64.b64encode(_PLACEHOLDER_SVG.encode()).decode()

# Status dot colour and label colour on white (all pass 4.5:1 contrast).
STATUS_COLOURS = {"Available": "#1E6B52", "Reserved": "#9A5B00", "Exchanged": "#5B6068"}

PAGE_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="st-"], .stApp, button, input, textarea {{ font-family: 'Inter', system-ui, sans-serif !important; }}
.stApp {{ background: {PAPER}; }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stSidebar"] {{ background: #FFFFFF; border-right: 1px solid {LINE}; }}
.block-container {{ padding-top: 2.2rem; max-width: 1180px; }}
.stButton > button, .stFormSubmitButton > button {{
  border-radius: 999px; min-height: 44px; font-weight: 500;
  border: 0; background: #F4F4F4; color: {INK};
}}
.stButton > button:hover {{ background: #E3F7EF; color: {INK}; }}
.stFormSubmitButton > button {{ background: {MINT}; color: {INK}; border-radius: 10px; width: 100%; font-size: 16px; }}
.stFormSubmitButton > button:hover {{ background: #45BF93; color: {INK}; }}
[data-testid="stWidgetLabel"] p {{ font-weight: 700; font-size: 15px; color: {INK}; }}
input, [data-baseweb="input"], [data-baseweb="select"] > div {{ border-radius: 9px !important; }}
[data-testid="stForm"] {{ background: #FFFFFF; border: 1px solid {LINE}; border-radius: 20px; padding: 22px; }}
.bs-card {{ background: #FFFFFF; border: 0; border-radius: 16px; padding: 12px; margin-bottom: 8px;
  box-shadow: 0 1px 2px rgba(20,24,30,0.05); }}
.bs-chip {{ display: inline-block; font-size: 12px; font-weight: 600; border-radius: 999px; padding: 3px 9px; margin: 0 4px 4px 0; }}
</style>
"""


def hero_html(title: str, subtitle: str) -> str:
    """Page heading with a short line under it."""
    return (
        f"<div style='margin-bottom:18px'>"
        f"<div style='font-size:30px;font-weight:800;letter-spacing:-0.5px;color:{INK}'>{html.escape(title)}</div>"
        f"<div style='font-size:15px;color:{MUTED};margin-top:4px'>{html.escape(subtitle)}</div></div>"
    )


def cover_html(link: str, max_width: int = 170) -> str:
    """A book-shaped cover box. The placeholder sits underneath the real cover, so if
    the cover link is missing or broken, the placeholder shows instead of a broken image."""
    layers, sizes = f"url('{PLACEHOLDER}')", "contain"
    if link and link.lower().startswith(("http://", "https://")):
        layers = f"url('{html.escape(link, quote=True)}'), {layers}"
        sizes = "cover, contain"
    return (
        f"<div style=\"width:100%;max-width:{max_width}px;aspect-ratio:2/3;margin:0 auto;"
        f"border-radius:10px;background-color:#E3F7EF;background-image:{layers};"
        f"background-size:{sizes};background-position:center;background-repeat:no-repeat;\"></div>"
    )


def price_text(book: pd.Series) -> str:
    """Price in rupees for Sell books; Lend and Swap have no price."""
    price = book.get("Price (Rs)")
    if book.get("Exchange Type") == "Sell" and pd.notna(price):
        return f"₹{int(price):,}"
    return "—"


def exchange_chip(book: pd.Series) -> str:
    """Lend / Swap / Sell label; Sell also shows the price."""
    kind = str(book["Exchange Type"])
    if kind == "Sell":
        return f"<span class='bs-chip' style='background:{MINT};color:{INK}'>Sell · {price_text(book)}</span>"
    return f"<span class='bs-chip' style='background:#E3F7EF;color:{GREEN}'>{html.escape(kind)}</span>"


def status_html(status: str) -> str:
    colour = STATUS_COLOURS.get(status, GREEN)
    return (
        f"<span style='font-size:12.5px;font-weight:600;color:{colour};display:inline-flex;align-items:center;gap:6px'>"
        f"<span style='width:7px;height:7px;border-radius:50%;background:{colour};display:inline-block'></span>"
        f"{html.escape(status)}</span>"
    )


def card_html(book: pd.Series) -> str:
    """One book card for the list: cover, title, author, condition, exchange type and status."""
    return f"""
<div class="bs-card">
  {cover_html(str(book["Cover Image Link"]))}
  <div style="font-weight:700;font-size:15px;color:{INK};margin-top:10px;line-height:1.3;height:2.6em;overflow:hidden;">{html.escape(str(book["Title"]))}</div>
  <div style="color:{MUTED};font-size:13px;margin:2px 0 8px;height:1.3em;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;">{html.escape(str(book["Author"]))}</div>
  <div><span class="bs-chip" style="background:#F4F4F4;color:#333333">{html.escape(str(book["Condition"]))}</span>{exchange_chip(book)}</div>
  <div style="margin-top:2px">{status_html(str(book["Status"]))}</div>
</div>"""


def details_html(book: pd.Series) -> str:
    """The detail rows shown when a book is opened (US01, acceptance criterion 3)."""
    rows = [
        ("Course", book["Course"]),
        ("Genre", book["Genre"]),
        ("Condition", book["Condition"]),
        ("Exchange type", book["Exchange Type"]),
        ("Price", price_text(book)),
        ("Owner", book["Owner Name"]),
        ("Book ID", book["Book ID"]),
    ]
    cells = "".join(
        f"<div style='display:flex;justify-content:space-between;gap:12px;padding:10px 0;border-bottom:1px solid {LINE}'>"
        f"<span style='color:{MUTED};font-size:14px'>{html.escape(label)}</span>"
        f"<span style='font-weight:600;font-size:14px;color:{INK};text-align:right'>{html.escape(str(value))}</span></div>"
        for label, value in rows
    )
    return (
        f"<div style='font-size:22px;font-weight:800;color:{INK};line-height:1.25'>{html.escape(str(book['Title']))}</div>"
        f"<div style='font-size:15px;color:{MUTED};margin:4px 0 10px'>by {html.escape(str(book['Author']))}</div>"
        f"<div style='margin-bottom:6px'>{status_html(str(book['Status']))}</div>{cells}"
    )
