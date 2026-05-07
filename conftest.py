"""
Shared pytest fixtures and helpers for the TrailTales Selenium suite.

A note on Selenium Manager:
    Selenium 4.10+ ships with "Selenium Manager", which auto-downloads the
    correct chromedriver / geckodriver for the browser installed on the
    machine. So you don't need webdriver-manager — just have Chrome (or
    Firefox) installed and Selenium handles the rest.
"""

from __future__ import annotations

import os
import string
import random
import time
from typing import Dict

import pytest
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load .env (BASE_URL, HEADLESS, BROWSER) once at import time.
load_dotenv()

DEFAULT_TIMEOUT = 15  # seconds — generous, since the React app boots client-side


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def base_url() -> str:
    url = os.getenv("BASE_URL", "http://localhost:5000").rstrip("/")
    return url


@pytest.fixture(scope="session", autouse=True)
def _verify_site_is_up(base_url):
    """Fail fast (with a clear message) if the site isn't reachable."""
    import requests
    try:
        r = requests.get(f"{base_url}/api/health", timeout=5)
        if r.status_code != 200:
            pytest.exit(
                f"\n[ABORT] {base_url}/api/health returned {r.status_code}. "
                f"Is TrailTales running at BASE_URL?\n",
                returncode=2,
            )
    except Exception as e:
        pytest.exit(
            f"\n[ABORT] Could not reach {base_url}. "
            f"Start the TrailTales container first (docker run ... -p 5000:5000 ...). "
            f"Underlying error: {e}\n",
            returncode=2,
        )


# ---------------------------------------------------------------------------
# Per-test driver
# ---------------------------------------------------------------------------

def _build_driver():
    browser = os.getenv("BROWSER", "chrome").lower()
    headless = os.getenv("HEADLESS", "true").lower() != "false"

    if browser == "firefox":
        opts = FirefoxOptions()
        if headless:
            opts.add_argument("-headless")
        driver = webdriver.Firefox(options=opts)
    else:
        opts = ChromeOptions()
        if headless:
            # The "new" headless mode in modern Chrome behaves like a real browser.
            opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1366,900")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        # Suppress noisy DevTools logs on Windows
        opts.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(options=opts)

    driver.set_page_load_timeout(30)
    return driver


@pytest.fixture
def driver():
    """Fresh browser per test. Closes automatically afterwards."""
    drv = _build_driver()
    yield drv
    drv.quit()


# ---------------------------------------------------------------------------
# Test data + helpers
# ---------------------------------------------------------------------------

def _rand_suffix(n: int = 8) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choices(alphabet, k=n))


@pytest.fixture
def unique_user() -> Dict[str, str]:
    """A throwaway user with a unique username so tests don't collide."""
    suffix = _rand_suffix()
    return {
        "name": f"Test User {suffix}",
        "username": f"tu_{suffix}",        # matches the [a-zA-Z0-9_]{3,24} pattern
        "password": "supersecret123",
    }


def wait_for(driver, locator, timeout: int = DEFAULT_TIMEOUT):
    """Wait until an element is visible and return it."""
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located(locator)
    )


def wait_clickable(driver, locator, timeout: int = DEFAULT_TIMEOUT):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable(locator)
    )


def wait_url_contains(driver, fragment: str, timeout: int = DEFAULT_TIMEOUT):
    WebDriverWait(driver, timeout).until(EC.url_contains(fragment))


# --- Auth helpers -----------------------------------------------------------

def signup_via_ui(driver, base_url: str, user: Dict[str, str]) -> None:
    """Sign a user up through the Signup form. Leaves driver on /dashboard."""
    driver.get(f"{base_url}/signup")
    wait_for(driver, (By.CSS_SELECTOR, "form input"))
    inputs = driver.find_elements(By.CSS_SELECTOR, "form input")
    # Order: name, username, password (matches Signup.jsx)
    inputs[0].send_keys(user["name"])
    inputs[1].send_keys(user["username"])
    inputs[2].send_keys(user["password"])

    driver.find_element(By.CSS_SELECTOR, "form button.btn-primary").click()
    wait_url_contains(driver, "/dashboard")


def login_via_ui(driver, base_url: str, user: Dict[str, str]) -> None:
    """Log a user in. Leaves driver on /dashboard."""
    driver.get(f"{base_url}/login")
    wait_for(driver, (By.CSS_SELECTOR, "form input"))
    inputs = driver.find_elements(By.CSS_SELECTOR, "form input")
    # Order: username, password (matches Login.jsx)
    inputs[0].send_keys(user["username"])
    inputs[1].send_keys(user["password"])
    driver.find_element(By.CSS_SELECTOR, "form button.btn-primary").click()
    wait_url_contains(driver, "/dashboard")


def logout_via_ui(driver) -> None:
    """Click the navbar "Sign out" button."""
    btn = wait_clickable(
        driver, (By.XPATH, "//button[contains(., 'Sign out')]")
    )
    btn.click()
    # After logout the navbar should show "Sign in" again
    WebDriverWait(driver, DEFAULT_TIMEOUT).until(
        EC.presence_of_element_located(
            (By.XPATH, "//a[contains(., 'Sign in')]")
        )
    )
