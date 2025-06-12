from datetime import datetime, timedelta

from django.test import LiveServerTestCase
from playwright.async_api import expect, async_playwright

from app.models import Event, User, Venue


class TicketE2ETest(LiveServerTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='e2euser', password='1234')
        venue = Venue.objects.create(
            name="Test Venue", address="Calle Falsa", city="Ciudad", capacity=100,
            contact_info="info@test.com", created_by=self.user
        )
        self.event = Event.objects.create(
            title="Evento E2E",
            description="Descripción",
            scheduled_at=datetime.now() + timedelta(days=5),
            organizer=self.user,
            venue=venue
        )

    async def test_resumen_actualiza_con_js(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            await page.goto(f"{self.live_server_url}/accounts/login/")
            await page.fill('input[name="username"]', 'e2euser')
            await page.fill('input[name="password"]', '1234')
            await page.click('button[type="submit"]')

            await page.goto(f"{self.live_server_url}/tickets/new/")
            await page.fill('#id_quantity', '4')
            await page.select_option('#id_type', 'VIP')
            await page.wait_for_timeout(500)

            await expect(page.locator('#total')).to_have_text('$440.00')

            await browser.close()