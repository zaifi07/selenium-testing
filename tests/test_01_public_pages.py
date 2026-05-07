"""
Public-facing pages: home, blog list, footer, 404.
No authentication required.
"""

import pytest
from selenium.webdriver.common.by import By

from conftest import wait_for, wait_clickable, wait_url_contains


# ---------------------------------------------------------------------------
# 1. Home page
# ---------------------------------------------------------------------------

@pytest.mark.smoke
def test_home_page_loads_with_hero(driver, base_url):
    """Hitting / should render the hero with the brand title."""
    driver.get(f"{base_url}/")
    h1 = wait_for(driver, (By.CSS_SELECTOR, "section.hero h1"))
    assert "Explore the world" in h1.text
    # Title tag should be set by Vite
    assert driver.title  # not empty


@pytest.mark.smoke
def test_home_has_explore_and_join_ctas(driver, base_url):
    """Hero should expose 'Start exploring' (-> /blog) and 'Join the community' (-> /signup)."""
    driver.get(f"{base_url}/")
    explore = wait_clickable(driver, (By.LINK_TEXT, "Start exploring"))
    join = driver.find_element(By.LINK_TEXT, "Join the community")
    assert explore.get_attribute("href").endswith("/blog")
    assert join.get_attribute("href").endswith("/signup")


def test_home_join_button_navigates_to_signup(driver, base_url):
    driver.get(f"{base_url}/")
    wait_clickable(driver, (By.LINK_TEXT, "Join the community")).click()
    wait_url_contains(driver, "/signup")
    assert "/signup" in driver.current_url


# ---------------------------------------------------------------------------
# 2. Blog list page
# ---------------------------------------------------------------------------

@pytest.mark.smoke
def test_blog_list_page_loads(driver, base_url):
    """/blog should render the 'The Blog' heading and a search box."""
    driver.get(f"{base_url}/blog")
    heading = wait_for(driver, (By.XPATH, "//h2[normalize-space()='The Blog']"))
    assert heading.is_displayed()
    search_box = driver.find_element(By.CSS_SELECTOR, "input[type='search']")
    assert search_box.is_displayed()


def test_blog_search_with_no_matches_shows_empty_state(driver, base_url):
    """Searching for an absurd string should render the 'No posts found' message."""
    driver.get(f"{base_url}/blog")
    search_box = wait_for(driver, (By.CSS_SELECTOR, "input[type='search']"))
    search_box.send_keys("zz_no_such_post_zz_xyz_123")
    driver.find_element(By.XPATH, "//button[normalize-space()='Search']").click()
    wait_url_contains(driver, "q=zz_no_such_post")
    msg = wait_for(driver, (By.CSS_SELECTOR, ".center-msg"))
    assert "No posts found" in msg.text


# ---------------------------------------------------------------------------
# 3. 404 / not-found
# ---------------------------------------------------------------------------

def test_404_page_for_unknown_route(driver, base_url):
    driver.get(f"{base_url}/this-page-does-not-exist-xyz")
    eyebrow = wait_for(driver, (By.XPATH, "//div[normalize-space()='404']"))
    assert eyebrow.is_displayed()
    # And the friendly message
    body = driver.find_element(By.TAG_NAME, "body").text
    assert "doesn't lead anywhere" in body or "wandered off" in body
