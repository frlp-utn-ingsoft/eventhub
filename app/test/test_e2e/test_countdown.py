import re
import pytest
from playwright.sync_api import sync_playwright

# Helper para login simple (adaptar a tu forma real de login)
def login(page, username, password):
    page.goto("http://localhost:8000/accounts/login/")  # URL correcta de login
    page.fill("input[name='username']", username)
    page.fill("input[name='password']", password)
    page.click("button[type='submit']")
    # Esperar a que redirija, o que alguna señal de login exista
    page.wait_for_url("http://localhost:8000/")  # Adaptar a url post-login

@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p

@pytest.fixture
def browser(playwright_instance):
    browser = playwright_instance.chromium.launch(headless=True)
    yield browser
    browser.close()

def test_countdown_visibility_for_non_organizer(browser):
    page = browser.new_page()

    # Login como usuario no organizador (crear previamente o usar fixture)
    login(page, "usuario", "password")

    event_id = 123  # Cambiar por evento válido en tu DB de test
    page.goto(f"http://localhost:8000/events/{event_id}/")

    countdown = page.locator("#countdown")
    assert countdown.is_visible()

    text = countdown.text_content()
    assert re.match(r"\d{1,2}:\d{2}:\d{2}", text)

    initial_text = text
    page.wait_for_timeout(2000)  # Esperar 2 segundos
    new_text = countdown.text_content()
    assert new_text != initial_text

def test_countdown_not_visible_for_organizer(browser):
    page = browser.new_page()

    # Login como usuario organizador
    login(page, "organizador", "password")

    event_id = 123  # Mismo evento de arriba
    page.goto(f"http://localhost:8000/events/{event_id}/")

    countdown = page.locator("#countdown")
    assert countdown.count() == 0  # No debe existir ni ser visible
