"""
Navbar / footer behavior + a tiny API smoke check via Selenium.
"""

import json

import pytest
from selenium.webdriver.common.by import By

from conftest import wait_for, wait_clickable, wait_url_contains


def test_navbar_shows_signin_and_join_when_logged_out(driver, base_url):
    driver.get(f"{base_url}/")
    wait_for(driver, (By.CSS_SELECTOR, "header.nav"))
    assert driver.find_element(By.LINK_TEXT, "Sign in").is_displayed()
    assert driver.find_element(By.LINK_TEXT, "Join").is_displayed()
    # Dashboard / Write should not appear yet
    assert not driver.find_elements(By.LINK_TEXT, "Dashboard")
    assert not driver.find_elements(By.LINK_TEXT, "Write")


def test_navbar_logo_links_back_home(driver, base_url):
    driver.get(f"{base_url}/blog")
    wait_clickable(driver, (By.CSS_SELECTOR, "a.nav-logo")).click()
    wait_url_contains(driver, base_url)
    # On home, the hero h1 should be visible again
    h1 = wait_for(driver, (By.CSS_SELECTOR, "section.hero h1"))
    assert h1.is_displayed()


def test_footer_renders_brand_and_links(driver, base_url):
    driver.get(f"{base_url}/")
    footer = wait_for(driver, (By.CSS_SELECTOR, "footer.footer"))
    text = footer.text
    assert "TrailTales" in text
    assert "All journeys reserved" in text
    # The "All stories" link should exist and point to /blog
    all_stories = footer.find_element(By.LINK_TEXT, "All stories")
    assert all_stories.get_attribute("href").endswith("/blog")


def test_health_endpoint_returns_ok(driver, base_url):
    """Hit /api/health through the browser and confirm the JSON looks right."""
    driver.get(f"{base_url}/api/health")
    body_text = driver.find_element(By.TAG_NAME, "body").text
    payload = json.loads(body_text)
    assert payload.get("ok") is True
    assert payload.get("service") == "TrailTales"
