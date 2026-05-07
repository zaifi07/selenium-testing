"""
Full post lifecycle for an authenticated user:
    create -> appears in /blog -> edit -> delete

These tests share a module-scoped browser so the user (and the post)
persists across them. Each test assertion is still independent.
"""

import string
import random

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import conftest as cf


# ---------------------------------------------------------------------------
# Module-scoped fixtures: ONE browser, ONE user, ONE post for this whole file
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def authed_driver(base_url):
    drv = cf._build_driver()
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    user = {
        "name": f"Crud User {suffix}",
        "username": f"crud_{suffix}",
        "password": "supersecret123",
    }
    cf.signup_via_ui(drv, base_url, user)
    yield drv
    drv.quit()


@pytest.fixture(scope="module")
def post_data():
    suffix = "".join(random.choices(string.ascii_lowercase, k=6))
    return {
        "title": f"Selenium Test Story {suffix}",
        "location": "Reykjavík, Iceland",
        "tags": "selenium, automated, test",
        "excerpt": "A story written by a robot.",
        "content": (
            "This is the body of an automated Selenium test post. "
            "It exists to verify that creating, listing, editing and "
            "deleting posts all work correctly."
        ),
        "edited_marker": f"EDITED-{suffix}",
    }


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

@pytest.mark.crud
def test_create_post_redirects_to_blog_detail(authed_driver, base_url, post_data):
    """Submitting the Create form should land on /blog/<id> with the new title."""
    drv = authed_driver
    drv.get(f"{base_url}/create")

    cf.wait_for(drv, (By.NAME, "title")).send_keys(post_data["title"])
    drv.find_element(By.NAME, "location").send_keys(post_data["location"])
    drv.find_element(By.NAME, "tags").send_keys(post_data["tags"])
    drv.find_element(By.NAME, "excerpt").send_keys(post_data["excerpt"])
    drv.find_element(By.NAME, "content").send_keys(post_data["content"])

    drv.find_element(By.CSS_SELECTOR, "form button.btn-primary").click()

    # Wait until URL becomes /blog/<24-hex-mongo-id>
    WebDriverWait(drv, cf.DEFAULT_TIMEOUT).until(
        lambda d: "/blog/" in d.current_url and d.current_url.rstrip("/").split("/")[-1] != "blog"
    )

    h1 = cf.wait_for(drv, (By.CSS_SELECTOR, ".post-hero-inner h1"))
    assert post_data["title"] in h1.text

    # Stash the post URL on the post_data dict so later tests can reuse it.
    post_data["url"] = drv.current_url
    post_data["id"] = drv.current_url.rstrip("/").split("/")[-1]


@pytest.mark.crud
def test_created_post_is_visible_in_blog_list(authed_driver, base_url, post_data):
    """The post we just created should appear when we search for its title."""
    assert "url" in post_data, "create test must run first"
    drv = authed_driver
    drv.get(f"{base_url}/blog")
    search = cf.wait_for(drv, (By.CSS_SELECTOR, "input[type='search']"))
    search.send_keys(post_data["title"])
    drv.find_element(By.XPATH, "//button[normalize-space()='Search']").click()

    # Wait for the title to appear somewhere on the page
    WebDriverWait(drv, cf.DEFAULT_TIMEOUT).until(
        EC.text_to_be_present_in_element((By.TAG_NAME, "body"), post_data["title"])
    )


# ---------------------------------------------------------------------------
# EDIT
# ---------------------------------------------------------------------------

@pytest.mark.crud
def test_edit_own_post_updates_content(authed_driver, base_url, post_data):
    """Open the post -> click Edit -> change content -> save -> verify."""
    assert "url" in post_data, "create test must run first"
    drv = authed_driver
    drv.get(post_data["url"])

    cf.wait_clickable(drv, (By.LINK_TEXT, "Edit")).click()
    cf.wait_url_contains(drv, "/edit/")

    content = cf.wait_for(drv, (By.NAME, "content"))
    content.clear()
    new_body = f"{post_data['content']} -- {post_data['edited_marker']}"
    content.send_keys(new_body)

    drv.find_element(By.CSS_SELECTOR, "form button.btn-primary").click()
    cf.wait_url_contains(drv, f"/blog/{post_data['id']}")

    body_text = cf.wait_for(drv, (By.CSS_SELECTOR, ".post-body")).text
    assert post_data["edited_marker"] in body_text


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

@pytest.mark.crud
def test_delete_own_post_removes_it(authed_driver, base_url, post_data):
    """Click delete, accept the JS confirm dialog, end up back on /blog."""
    assert "url" in post_data, "create test must run first"
    drv = authed_driver
    drv.get(post_data["url"])

    cf.wait_clickable(
        drv, (By.XPATH, "//button[contains(@class,'btn-danger') and contains(., 'Delete')]")
    ).click()

    # JS window.confirm() — accept it
    WebDriverWait(drv, cf.DEFAULT_TIMEOUT).until(EC.alert_is_present())
    drv.switch_to.alert.accept()

    cf.wait_url_contains(drv, "/blog")
    # Direct visit should now show "Post not found."
    drv.get(post_data["url"])
    msg = cf.wait_for(drv, (By.CSS_SELECTOR, ".center-msg"))
    assert "not found" in msg.text.lower()
