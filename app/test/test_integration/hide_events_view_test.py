from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from app.models import Event, User
import datetime

class HideEventsViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="viewer", password="12345")
        self.client.login(username="viewer", password="12345")
        self.future_event = Event.objects.create(
            title="Futuro",
            description="Evento futuro",
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            organizer=self.user
        )
        self.past_event = Event.objects.create(
            title="Pasado",
            description="Evento pasado",
            scheduled_at=timezone.now() - datetime.timedelta(days=2),
            organizer=self.user
        )

    def test_only_future_events_shown_by_default(self):
        response = self.client.get(reverse("events"))
        self.assertContains(response, self.future_event.title)
        self.assertNotContains(response, self.past_event.title)
