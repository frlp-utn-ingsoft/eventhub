import datetime

from django.test import TestCase
from django.utils import timezone

from app.models import Category, Event, User


class EventModelTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador_test",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )

        cat = Category.objects.create(name="General")

        now = timezone.now()
        self.past_event_1 = Event.objects.create(
            title="Pasado 1", description="...", scheduled_at=now - datetime.timedelta(days=1), organizer=self.organizer
        )
        self.past_event_2 = Event.objects.create(
            title="Pasado 2", description="...", scheduled_at=now - datetime.timedelta(days=2), organizer=self.organizer
        )
        self.future_event_1 = Event.objects.create(
            title="Futuro 1", description="...", scheduled_at=now + datetime.timedelta(days=1), organizer=self.organizer
        )
        self.future_event_2 = Event.objects.create(
            title="Futuro 2", description="...", scheduled_at=now + datetime.timedelta(days=2), organizer=self.organizer
        )
        self.future_event_3 = Event.objects.create(
            title="Futuro 3", description="...", scheduled_at=now + datetime.timedelta(days=2), organizer=self.organizer
        )
        self.past_event_1.categories.add(cat)
        self.past_event_2.categories.add(cat)
        self.future_event_1.categories.add(cat)
        self.future_event_2.categories.add(cat)
    
    def test_get_upcoming_events(self):
        qs = Event.get_upcoming_events()
        self.assertEqual(len(qs), 3)
        self.assertIn(self.future_event_1, qs)
        self.assertIn(self.future_event_2, qs)
        self.assertIn(self.future_event_3, qs)
        self.assertNotIn(self.past_event_1, qs)
        self.assertNotIn(self.past_event_2, qs)

    def test_get_all_events(self):
        qs = Event.get_all_events()
        self.assertEqual(len(qs), 5)
        self.assertIn(self.future_event_1, qs)
        self.assertIn(self.future_event_2, qs)
        self.assertIn(self.past_event_1, qs)
        self.assertIn(self.past_event_2, qs)