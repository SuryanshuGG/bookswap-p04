"""Small pieces of page layout: the book card and the cover image."""

import base64
import html

import pandas as pd

# Shown when a book has no cover link, or when its link stops working
# (US01, acceptance criterion 4).
_PLACEHOLDER_SVG = """<svg xmlns='http://www.w3.org/2000/svg' width='300' height='450' viewBox='0 0 300 450'>
<rect width='300' height='450' fill='#E8F7F1'/>
<rect x='60' y='120' width='180' height='210' rx='10' fill='none' stroke='#57CFA4' stroke-width='8'/>
<line x1='100' y1='180' x2='200' y2='180' stroke='#57CFA4' stroke-width='8'/>
<line x1='100' y1='220' x2='200' y2='220' stroke='#57CFA4' stroke-width='8'/>
<line x1='100' y1='260' x2='170' y2='260' stroke='#57CFA4' stroke-width='8'/>
<text x='150' y='380' font-family='sans-serif' font-size='26' fill='#2E7D61' text-anchor='middle'>No cover</text>
</svg>"""
PLACEHOLDER = "data:image/svg+xml;base64," + base64.b64encode(_PLACEHOLDER_SVG.encode()).decode()

STATUS_COLOURS = {"Available": "#2E7D61", "Reserved": "#B26A00", "Exchanged": "#6B6B6B"}


def cover_html(link: str, max_width: int = 170) -> str:
    """A book-shaped cover box. The placeholder sits underneath the real cover, so if
    the cover link is missing or broken, the placeholder shows instead of a broken image."""
    layers, sizes = f"url('{PLACEHOLDER}')", "contain"
    if link and link.lower().startswith(("http://", "https://")):
        layers = f"url('{html.escape(link, quote=True)}'), {layers}"
        sizes = "cover, contain"
    return (
        f"<div style=\"width:100%;max-width:{max_width}px;aspect-ratio:2/3;margin:0 auto;"
        f"border-radius:10px;background-color:#E8F7F1;background-image:{layers};"
        f"background-size:{sizes};background-position:center;background-repeat:no-repeat;\"></div>"
    )


def price_text(book: pd.Series) -> str:
    """Price in rupees for Sell books; Lend and Swap have no price."""
    price = book.get("Price (Rs)")
    if book.get("Exchange Type") == "Sell" and pd.notna(price):
        return f"₹{int(price):,}"
    return "—"


def card_html(book: pd.Series) -> str:
    """One book card for the list: cover, title, author, condition and status."""
    status = str(book["Status"])
    colour = STATUS_COLOURS.get(status, "#2E7D61")
    return f"""
<div style="border:1px solid #E3E3E3;border-radius:12px;padding:10px;margin-bottom:6px;background:#FFFFFF;">
  {cover_html(str(book["Cover Image Link"]))}
  <div style="font-weight:600;font-size:0.95rem;margin-top:8px;line-height:1.25;height:2.5em;overflow:hidden;">{html.escape(str(book["Title"]))}</div>
  <div style="color:#5F5F5F;font-size:0.82rem;height:1.3em;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;">{html.escape(str(book["Author"]))}</div>
  <div style="margin-top:6px;font-size:0.78rem;">
    <span style="background:#E8F7F1;color:#2E7D61;border-radius:999px;padding:2px 8px;">{html.escape(str(book["Condition"]))}</span>
    <span style="color:{colour};margin-left:6px;">● {html.escape(status)}</span>
  </div>
</div>"""
