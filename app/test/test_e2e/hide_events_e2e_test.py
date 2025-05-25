from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from app.models import Event, User
import datetime

class HideEventsE2ETest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="e2euser", password="12345")
        self.client.login(username="e2euser", password="12345")
        self.future_event = Event.objects.create(
            title="Futuro E2E",
            description="Evento futuro",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.user
        )
        self.past_event = Event.objects.create(
            title="Pasado E2E",
            description="Evento pasado",
            scheduled_at=timezone.now() - datetime.timedelta(days=1),
            organizer=self.user
        )

    def test_show_past_events_checkbox(self):
        response = self.client.get(reverse("events") + "?show_past=1")
        self.assertContains(response, self.past_event.title)
        self.assertContains(response, self.future_event.title)
