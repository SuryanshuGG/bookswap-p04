# BookSwap: campus book exchange (P04)

XIME Bangalore, PGDM Agile project, Group 2 / Team 3.

BookSwap lets students list, find and request books from each other on campus.

**Live app:** https://bookswap-p04-atuq2z9hmqnqmnc3rvgxzt.streamlit.app/

## Team

| Name | Role |
|---|---|
| Chandana | Product Owner |
| Riya | Scrum Master |
| Suryanshu | Builder |
| Krishna | Builder |
| Nandan | Tester |
| Suranjana | Content |
| Swasti | Designer |

## The problem

Course books at XIME are used for one term and then sit on a shelf, while juniors buy the same titles new.
BookSwap lets students swap, lend, sell or donate those books to each other on campus, safely and only with verified XIME accounts.

## Stories delivered (15 of 15)

| Story | What it does | Where to see it in the app | Tested in |
|---|---|---|---|
| P04-US01 Load 40 sample books | 40 books with covers, details and owner | Browse books | Sprint 1 |
| P04-US02 List a book | Photo, condition, Swap / Lend / Sell (price for Sell) | + List a book | TC01-TC04 |
| P04-US03 Search | Title or author, part words, any capitals | Search box on Browse | TC05-TC08 |
| P04-US04 Filter | Course, genre and exchange type, alone or together | Filters on Browse | TC13 |
| P04-US05 Request a book | Swap offer, pay-at-handover note, My Requests | View details → Request this book | TC09-TC12, TC14-TC16 |
| P04-US06 Test listing, search and request | Sprint 1 test sheet | `docs/testing/` | TC01-TC18 |
| P04-US07 Accept or decline | Reserved, return date for Lend, edit / pause / delete | My Listings | TC17-TC18 |
| P04-US08 Campus handover | Approved points, future time, messages, both confirm → Exchanged, Paid, return reminder, Returned | Handover card under an accepted request | TC33-TC36 |
| P04-US09 Rate, report, verified sign-in | Rate once after an exchange, profile average, Report, Firebase email verification | Handover card, My profile, Report this listing, Sign in | TC37-TC41 |
| P04-US10 Wishlist | Save a book, Now Available match, badge | Wishlist | TC19-TC22 |
| P04-US11 Guidelines and how-to | Fair pricing, condition, safe meeting, approved points, 5 steps | Help | Coordinator approval |
| P04-US12 Usability test | Six students, task script and results | `docs/usability/` | BS-47, BS-48 |
| P04-US13 Reading circle announcements | Coordinator posts; home screen, soonest first; past events hidden | Home screen, Coordinator | TC23-TC25 |
| P04-US14 Donate a book | Donate, can't be requested, coordinator Received, withdraw | My Listings, Coordinator | TC29-TC32 |
| P04-US15 Peer reviews | Stars, 100 words, one review per student | View details → Reviews | TC26-TC28 |

## Try it (demo accounts)

- Students: sign in with your name and @xime.org email (or email and password once Firebase is on).
- Coordinator tools: sign in as Chandana (Product Owner) and tap **Coordinator**.
- Data is saved in the team's Google Sheet: Books, Users, Requests, Wishlist, Announcements, Handovers, Messages, Reviews, Donations, Ratings and Reports tabs.

## Switch on email verification (US09 criteria 7 to 9)

1. In the Firebase console, open the project → **Authentication → Sign-in method** → enable **Email/Password**.
2. In **Project settings → General**, copy the **Web API key**.
3. In Streamlit → app **Settings → Secrets**, add one line: `firebase_api_key = "the key"` and save.
4. Make sure each student's name (and roll number, in a **Roll Number** column) is on the Users tab. Sign-up is refused for anyone else.

## Run it on your own computer

1. Install Python 3.11 or newer.
2. In this folder, run `pip install -r requirements.txt`.
3. Run `streamlit run app.py` and open the link it prints.

## Where things are

- `app.py`: the app's pages
- `bookswap/data.py`: reads books and users from the Excel file
- `bookswap/ui.py`: the book card and cover image
- `bookswap/users.py`: who can sign in, and sign-up for new students
- `bookswap/search.py`: search by title or author
- `bookswap/filters.py`: course and genre filters
- `bookswap/requests.py`: request rules, swap offers and saving requests
- `bookswap/listings.py`: the listing rules, and reading and saving books
- `bookswap/handover.py`, `ratings.py`, `auth.py`: handover, rating and report, verified sign-in (Sprint 2)
- `bookswap/wishlist.py`, `reviews.py`, `donations.py`, `announcements.py`, `help.py`: the other Sprint 2 stories
- `bookswap/sheet_tabs.py`: shared saving for the Sprint 2 Google Sheet tabs
- `tests/`: automatic checks (run `python -m pytest tests`)
- `data/BookSwap_40_Books.xlsx`: the 40 sample books, users and lists
- `docs/ai-usage-log.md`: what was written with AI help, task by task
- `docs/screenshots/`: screenshots attached to each pull request
- `docs/testing/`: test sheets with recorded results (Sprint 1 TC01-TC18, Sprint 2 TC19-TC41)
- `docs/usability/`: usability task script and recording sheet
- `docs/po-acceptance.md`: how the Product Owner accepted each story

## Working rules

- Every branch, commit and pull request starts with its Jira key, for example `BS-5 Show book list with cover and title`.
- A builder reviews and merges every pull request.
- No passwords or keys in this repo. They go in Streamlit's secrets settings (see `.streamlit/secrets.toml.example`).

## Credits

- Title page photo: [Tom Hermans on Unsplash](https://unsplash.com/photos/book-lot-on-table-9BoqXzEeQqM), free to use under the Unsplash License.
