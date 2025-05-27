import pytest
from app.models import User  # Importa tu User personalizado
from playwright.sync_api import sync_playwright

@pytest.mark.django_db
def test_refund_creation_block_if_pending_e2e(live_server):
    # Crear usuario con contraseña
    User.objects.create_user(username='jano_user', password='123456789')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(f"{live_server.url}/accounts/login/")

        page.fill('input[name="username"]', 'jano_user')
        page.fill('input[name="password"]', '123456789')
        page.click('button[type="submit"]')

        page.wait_for_load_state("networkidle")

        assert "/events" in page.url, f"Expected to be in /events but current URL is {page.url}"
