from django.utils.timezone import now, timedelta
from app.models import Event, User
from .base import BaseE2ETest
from playwright.sync_api import expect  # type: ignore

class HidePastEventsE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()
        self.user = self.create_test_user()

        self.future_event = Event.objects.create(
            title="Evento Futuro",
            description="Este es un evento futuro",
            scheduled_at=now() + timedelta(days=2),
            organizer=self.user
        )

        self.past_event = Event.objects.create(
            title="Evento Pasado",
            description="Este es un evento pasado",
            scheduled_at=now() - timedelta(days=2),
            organizer=self.user
        )

    def test_hide_past_events_by_default(self):
        self.login_user("usuario_test", "password123")

        self.page.goto(f"{self.live_server_url}/events/")

        # Evento futuro visible, evento pasado oculto
        expect(self.page.get_by_role("cell", name="Evento Futuro", exact=True)).to_be_visible()
        expect(self.page.locator("text=Evento Pasado")).not_to_be_visible()

    def test_show_past_events_when_checkbox_checked(self):
        self.login_user("usuario_test", "password123")

        self.page.goto(f"{self.live_server_url}/events/?show_past=1")

        # Ambos eventos visibles
        expect(self.page.get_by_role("cell", name="Evento Futuro", exact=True)).to_be_visible()
        expect(self.page.get_by_role("cell", name="Evento Pasado", exact=True)).to_be_visible()
