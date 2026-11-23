"""Exchange guidelines, how-to guide and approved handover points (story P04-US11).

Text by Suranjana (BS-44 guidelines, BS-45 how-to, BS-38 handover points),
approved by the literary club coordinator before release (criterion 5).
The handover points are also used by the handover screen in P04-US08.
"""

# BS-38: public places on campus where students may hand over books.
HANDOVER_POINTS = [
    ("Library entrance", "Main library, by the front desk"),
    ("Cafeteria", "Main canteen, by the billing counter"),
    ("Academic block lobby", "Ground floor reception"),
    ("Hostel reception", "Common lobby, visitors' area"),
]
HANDOVER_HOURS = "8:00 am to 8:00 pm"

# BS-44: exchange guidelines (criteria 1 and 3).
GUIDELINES = [
    ("Fair pricing", [
        "Sell: ask no more than half the printed price for a Like New copy, and less for Good or Fair.",
        "Lend: lending is always free. Agree a return date of 60 days or less.",
        "Swap: one book for one book. Agree which book you offer before you meet.",
        "No deposits, extra fees or advance payments.",
    ]),
    ("Book condition", [
        "Like New: no marks or highlights, cover and spine as new.",
        "Good: light wear, a few notes or highlights.",
        "Fair: heavy notes or a worn cover, but every page is there.",
        "Your photo must show your own copy. Mention any missing or damaged pages.",
    ]),
    ("Safe meeting", [
        "Meet only at an approved handover point, from " + HANDOVER_HOURS + ".",
        "Agree the place and time in the app, so both of you see the same plan.",
        "Check the book before you pay. Pay the owner at handover by UPI or cash, never in advance.",
        "Never share an OTP, PIN or bank password with anyone.",
        "If something feels wrong, leave, and use Report in the app.",
    ]),
    ("Being a good member", [
        "Be on time. If you can't come, tell the other student in the app.",
        "Return lent books on time and in the same condition.",
        "Rate your exchange partner honestly after each exchange.",
        "Donated books go to the department library and are not for resale.",
    ]),
]

# BS-45: how to list and request a book, in five steps (criterion 2).
HOW_TO = [
    ("Sign in", "Use your name and your @xime.org email."),
    ("List a book", "Tap + List a book. Add the title, author, course, genre, a photo, the condition and "
                    "Swap, Lend or Sell (with a price for Sell)."),
    ("Find a book", "Search by title or author, or filter by course, genre and exchange type. "
                    "Tap View details to see the book."),
    ("Request it", "Tap Request this book. For a Swap, choose one of your books to offer. "
                   "Follow it in My Requests."),
    ("Meet and exchange", "When the owner accepts, meet at an approved handover point, check the book, "
                          "pay if it's a Sell, and exchange."),
]


def handover_point_names() -> list[str]:
    """Names only, for the handover point picker in P04-US08."""
    return [name for name, _ in HANDOVER_POINTS]
