"""
Auth flows: signup, login (good + bad), logout, route protection.
"""

import pytest
from selenium.webdriver.common.by import By

from conftest import (
    wait_for,
    wait_clickable,
    wait_url_contains,
    signup_via_ui,
    logout_via_ui,
)


# ---------------------------------------------------------------------------
# Signup
# ---------------------------------------------------------------------------


@pytest.mark.auth
@pytest.mark.smoke
def test_signup_success_redirects_to_dashboard(driver, base_url, unique_user):
    signup_via_ui(driver, base_url, unique_user)
    assert "/dashboard" in driver.current_url
    # Navbar should now show "Hi, <first name>"
    body = driver.find_element(By.TAG_NAME, "body").text
    assert f"Hi, {unique_user['name'].split()[0]}" in body


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@pytest.mark.auth
def test_login_with_invalid_credentials_shows_error(driver, base_url):
    driver.get(f"{base_url}/login")
    wait_for(driver, (By.CSS_SELECTOR, "form input"))
    inputs = driver.find_elements(By.CSS_SELECTOR, "form input")
    inputs[0].send_keys("nonexistent_user_xyz_999")
    inputs[1].send_keys("wrongpassword")
    driver.find_element(By.CSS_SELECTOR, "form button.btn-primary").click()

    err = wait_for(driver, (By.CSS_SELECTOR, ".error-msg"))
    assert err.text.strip()  # some error message is shown
    # Did NOT redirect
    assert "/login" in driver.current_url


@pytest.mark.auth
def test_login_after_signup_works(driver, base_url, unique_user):
    """Sign up, log out, then log back in via the login form."""
    signup_via_ui(driver, base_url, unique_user)
    logout_via_ui(driver)

    driver.get(f"{base_url}/login")
    wait_for(driver, (By.CSS_SELECTOR, "form input"))
    inputs = driver.find_elements(By.CSS_SELECTOR, "form input")
    inputs[0].send_keys(unique_user["username"])
    inputs[1].send_keys(unique_user["password"])
    driver.find_element(By.CSS_SELECTOR, "form button.btn-primary").click()

    wait_url_contains(driver, "/dashboard")
    body = driver.find_element(By.TAG_NAME, "body").text
    assert f"Hi, {unique_user['name'].split()[0]}" in body


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@pytest.mark.auth
def test_logout_clears_session_and_restores_signin_button(driver, base_url, unique_user):
    signup_via_ui(driver, base_url, unique_user)
    logout_via_ui(driver)
    # Sign-in button is back
    assert driver.find_element(By.LINK_TEXT, "Sign in").is_displayed()
    # Dashboard link is gone
    assert not driver.find_elements(By.LINK_TEXT, "Dashboard")


# ---------------------------------------------------------------------------
# Route protection
# ---------------------------------------------------------------------------

@pytest.mark.auth
def test_dashboard_redirects_to_login_when_logged_out(driver, base_url):
    driver.get(f"{base_url}/dashboard")
    wait_url_contains(driver, "/login")
    assert "/login" in driver.current_url


@pytest.mark.auth
def test_create_redirects_to_login_when_logged_out(driver, base_url):
    driver.get(f"{base_url}/create")
    wait_url_contains(driver, "/login")
    assert "/login" in driver.current_url
