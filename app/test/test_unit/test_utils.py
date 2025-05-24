from django.test import TestCase
from django.utils import timezone
from app.models import Event, User, Venue, Ticket
from app.utils import *
import datetime



class CountDownTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password"
        )
        self.venue_mocked = Venue.objects.create(
            name="Auditorio Nacional",
            address="60 y 124",
            capacity=5000,
            country="ARG",
            city="La Plata"
        )

    def test_count_down_with_empty_event(self):
        success, event = Event.new(
            title="Test Event",
            description="desc",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue_mocked,
            categories=[]
        )
        self.assertTrue(success)
    # Llamar a la función utils con `event`
    def test_count_down_with_future_event(self):
        pass
    def test_count_down_with_past_event(self):
        pass
    def test_count_down_with_unexistent(self):
        pass

