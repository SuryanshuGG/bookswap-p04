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

## What works so far

| Jira | Story | Status |
|---|---|---|
| BS-5 | P04-US01 Load 40 sample book listings: sign in, book list with cover and title, placeholder for missing covers, book details | Done |
| BS-55 | Sign-up for new students with name and college email (saved to the Google Sheet) | Done |
| BS-27 | P04-US03 Search books by title or author, with a wishlist message when nothing matches | In review |

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
- `tests/`: automatic checks (run `python -m pytest tests`)
- `data/BookSwap_40_Books.xlsx`: the 40 sample books, users and lists
- `docs/ai-usage-log.md`: what was written with AI help, task by task
- `docs/screenshots/`: screenshots attached to each pull request

## Working rules

- Every branch, commit and pull request starts with its Jira key, for example `BS-5 Show book list with cover and title`.
- A builder reviews and merges every pull request.
- No passwords or keys in this repo. They go in Streamlit's secrets settings (see `.streamlit/secrets.toml.example`).
