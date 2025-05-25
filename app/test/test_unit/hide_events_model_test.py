from django.test import TestCase
from django.utils import timezone
from app.models import Event, User
import datetime

class HideEventsModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="organizer", password="12345")
        self.future_event = Event.objects.create(
            title="Futuro",
            description="Evento futuro",
            scheduled_at=timezone.now() + datetime.timedelta(days=5),
            organizer=self.user
        )
        self.past_event = Event.objects.create(
            title="Pasado",
            description="Evento pasado",
            scheduled_at=timezone.now() - datetime.timedelta(days=5),
            organizer=self.user
        )

    def test_future_events_filtering(self):
        future_events = Event.objects.filter(scheduled_at__gte=timezone.now())
        self.assertIn(self.future_event, future_events)
        self.assertNotIn(self.past_event, future_events)
