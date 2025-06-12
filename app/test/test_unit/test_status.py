import datetime
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from app.models import Event, User, Venue 


class EventStatusUnitTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador_test",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )
        self.venue = Venue.objects.create(
            name="Test Venue",
            address="Test Address",
            city="Test City",
            capacity=100,
            contact_info="Test Info",
            created_by=self.organizer,
        )

        # test_status.py
    def create_event(self, **kwargs):
        default_data = {
            "title": "Test Event",
            "description": "Test Description",
            "scheduled_at": timezone.now() + datetime.timedelta(days=1),
            "organizer": self.organizer,
            "venue": self.venue,
            "available_tickets": self.venue.capacity
        }
        default_data.update(kwargs)
        return Event.objects.create(**default_data)

    def test_update_status_agotado(self):
        event = self.create_event(
            tickets_sold=self.venue.capacity,
            available_tickets=0 
        )
        event.update_status()
        self.assertEqual(event.status, "agotado")

    def test_update_status_activo_future(self):
        future_event = self.create_event(
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            tickets_sold=0,
            available_tickets=self.venue.capacity 
        )
        future_event.update_status()
        self.assertEqual(future_event.status, "activo")

    def test_update_status_activo_with_tickets_left(self):
        event = self.create_event(
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            tickets_sold=self.venue.capacity - 1,
            available_tickets=1 
        )
        event.update_status()
        self.assertEqual(event.status, "activo")

    def test_update_status_no_venue(self):
        event_no_venue = self.create_event(
            venue=None,
            available_tickets=0 
        )
        event_no_venue.update_status()
        self.assertEqual(event_no_venue.status, "sin lugar")