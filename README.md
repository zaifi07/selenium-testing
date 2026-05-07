# TrailTales — Selenium Test Suite

End-to-end browser tests for the [TrailTales](https://github.com/) blog
website, written in **Python + Selenium 4 + pytest**.

The suite drives a real browser (Chrome by default, Firefox optional) and
exercises every page of the running site: home, blog, signup/login,
post create/edit/delete, route protection, and the health endpoint.

> The application repo and this test repo are intentionally separate.
> This repo only contains tests — point it at any running TrailTales instance
> (local Docker, EC2, etc.) by setting `BASE_URL`.

---

## What it tests (21 tests across 4 files)

**`tests/test_01_public_pages.py`** — pages anyone can visit
1. Home page renders the hero
2. Hero shows the "Start exploring" + "Join the community" CTAs
3. Clicking "Join the community" navigates to `/signup`
4. `/blog` renders the heading and search box
5. Searching for nonsense shows the empty-state message
6. Unknown routes show the 404 page

**`tests/test_02_auth.py`** — accounts and route protection
7. Signup rejects passwords shorter than 6 chars
8. Successful signup redirects to `/dashboard` and greets the user
9. Login with bad credentials shows an error
10. Login after signup works
11. Logout restores the "Sign in" button and removes the Dashboard link
12. Visiting `/dashboard` while logged out redirects to `/login`
13. Visiting `/create` while logged out redirects to `/login`

**`tests/test_03_post_crud.py`** — full post lifecycle
14. Create post → redirected to `/blog/<id>` showing the new title
15. The new post appears when searched for on `/blog`
16. Editing the post persists the change
17. Deleting the post (handles the JS `confirm()` dialog) and confirms it's gone

**`tests/test_04_navigation_and_api.py`** — chrome and API smoke
18. Navbar shows Sign in / Join when logged out (no Dashboard / Write)
19. Logo link navigates back to home
20. Footer renders brand + working "All stories" link
21. `GET /api/health` returns valid JSON with `ok: true`

---

## Prerequisites

- **Python 3.10 or newer** (`python --version`)
- **Google Chrome** installed (or Firefox if you set `BROWSER=firefox`)
- The TrailTales website **already running** somewhere reachable from
  this machine — for example:
  ```bash
  docker run -p 5000:5000 trailtales
  # or:  http://<your-ec2-ip>:5000
  ```
  > Selenium 4.10+ ships with **Selenium Manager**, which auto-downloads
  > the matching `chromedriver` for your Chrome version. You do **not**
  > need to install chromedriver yourself.

---

## How to run (step by step)

```bash
# 1. Clone this repo
git clone <your-test-repo-url> trailtales-tests
cd trailtales-tests

# 2. Create + activate a virtualenv
python -m venv venv
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Tell the suite where the site is running
cp .env.example .env
# then edit .env and set BASE_URL=http://localhost:5000  (or your EC2 URL)

# 5. Make sure the site is up — this should return JSON:
#    curl http://localhost:5000/api/health

# 6. Run all tests
pytest
```

That's it. The suite will spin up a headless Chrome, run all 21 tests
against the URL in `BASE_URL`, and print a summary.

### Useful flags

```bash
pytest -v                       # verbose: one line per test
pytest tests/test_02_auth.py    # only one file
pytest -k "login"               # only tests whose name contains "login"
pytest -m smoke                 # only the smoke-marked tests (fast subset)
HEADLESS=false pytest           # show the browser while it runs
BROWSER=firefox pytest          # use Firefox instead of Chrome
pytest -x                       # stop at the first failure
```

### Configuration (.env)

| Variable   | Default                  | Meaning                                           |
|------------|--------------------------|---------------------------------------------------|
| `BASE_URL` | `http://localhost:5000`  | Where the running TrailTales site is reachable.   |
| `HEADLESS` | `true`                   | `false` opens a visible browser window.           |
| `BROWSER`  | `chrome`                 | `chrome` or `firefox`.                            |

You can also override per-run from the shell:
```bash
BASE_URL=http://3.110.45.12:5000 HEADLESS=false pytest
```

---

## Project layout

```
trailtales-tests/
├── README.md
├── requirements.txt
├── pytest.ini
├── .env.example
├── .gitignore
├── conftest.py                       # shared fixtures + signup/login helpers
└── tests/
    ├── __init__.py
    ├── test_01_public_pages.py
    ├── test_02_auth.py
    ├── test_03_post_crud.py
    └── test_04_navigation_and_api.py
```

Every test gets a fresh browser via the `driver` fixture (except the
post-CRUD file, which uses a module-scoped browser so create → edit →
delete share state on purpose).

Each test that needs an account uses the `unique_user` fixture, which
generates a random username/name so reruns don't collide.

---

## Troubleshooting

**`[ABORT] Could not reach http://localhost:5000`**
Your site isn't running, or `BASE_URL` is wrong. Start the container,
then verify with `curl $BASE_URL/api/health`.

**`SessionNotCreatedException: This version of ChromeDriver only supports Chrome version XX`**
Update Chrome to the latest stable, then re-run. Selenium Manager will
fetch a matching driver automatically.

**Tests hang on signup/login with HTTP 429**
The server has a rate limit of 50 auth requests / 15 minutes per IP.
If you re-run the suite many times in a row you can trip it. Wait
~15 minutes or restart the server (the limiter is in-memory).

**Headless Chrome behaves differently than visible Chrome**
Run with `HEADLESS=false` to watch what's happening — useful for
debugging selector or timing issues.

---

## CI hint

For GitHub Actions, a minimal job looks like:

```yaml
- uses: actions/setup-python@v5
  with: { python-version: "3.11" }
- run: pip install -r requirements.txt
- run: pytest
  env:
    BASE_URL: http://localhost:5000
    HEADLESS: "true"
```

(Spin the TrailTales container up in a previous step or as a service.)
