import re
from app.test.test_e2e.base import BaseE2ETest
from app.models import User, Event
from django.utils import timezone
from datetime import timedelta

class TestCountdownE2E(BaseE2ETest):
    def setUp(self):
        super().setUp()
        # Crear usuarios
        self.organizer = User.objects.create_user(username="organizador", password="password", is_organizer=True)
        self.usuario = User.objects.create_user(username="usuario", password="password")
        # Crear evento válido
        self.event = Event.objects.create(
            title="Evento Test",
            description="Descripción",
            scheduled_at=timezone.now() + timedelta(days=1),
            price_general=100,
            price_vip=200,
            tickets_total=100,
            tickets_sold=0,
            organizer=self.organizer,
        )

    def login(self, username, password):
        self.page.goto(f"{self.live_server_url}/accounts/login/")
        self.page.fill("input[name='username']", username)
        self.page.fill("input[name='password']", password)
        self.page.click("button[type='submit']")
        self.page.wait_for_load_state("networkidle")

    def test_countdown_visibility_for_non_organizer(self):
        self.login("usuario", "password")
        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/")
        countdown = self.page.locator("#countdown")
        countdown.wait_for(state="visible", timeout=5000)
        assert countdown.is_visible()
        text = countdown.text_content()
        assert text is not None
        assert re.match(r"\d+d \d+h \d+m \d+s", text)
        initial_text = text
        self.page.wait_for_timeout(2000)
        new_text = countdown.text_content()
        assert new_text is not None
        assert new_text != initial_text

    def test_countdown_not_visible_for_organizer(self):
        self.login("organizador", "password")
        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/")
        countdown = self.page.locator("#countdown")
        assert countdown.count() == 0
