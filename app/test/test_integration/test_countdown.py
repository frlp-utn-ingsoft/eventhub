import datetime
import time
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from app.models import Event, User, Venue
from datetime import datetime, timedelta

class CountdownTest(TestCase):
    """Base class with common setup for all event countdown tests"""

    def setUp(self):
        # Create an organizer user
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )

        # Create a regular user
        self.regular_user = User.objects.create_user(
            username="regular",
            email="regular@test.com",
            password="password123",
            is_organizer=False,
        )

        # Create a mock venue
        self.venue_mocked = Venue.objects.create(
            name="Auditorio Nacional",
            address="60 y 124",
            capacity=5000,
            country="ARG",  
            city="La Plata"
        )

        # Create a future event
        self.future_event = Event.objects.create(
            title="Evento 1",
            description="Descripción del evento 1",
            scheduled_at=timezone.now() + timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue_mocked
        )

        # Create a past event
        self.past_event = Event.objects.create(
            title="Evento 2",
            description="Descripción del evento 2",
            scheduled_at=timezone.now() - timedelta(days=2),
            organizer=self.organizer,
            venue=self.venue_mocked
        )

        # Client for making requests
        self.client = Client()


class CountdownTestVisualization(CountdownTest):
    """Tests for the event detail view"""

    def test_future_event_detail_shows_countdown_for_non_organizer(self):
        # Verify that a non-organizer user sees the countdown for a future event
        self.client.login(username=self.regular_user.username, password="password123")
        response = self.client.get(f'/events/{self.future_event.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cuenta Regresiva')
        self.assertFalse(response.context["user_is_organizer"])

    def test_past_event_detail_dont_shows_countdown_for_non_organizer(self):
        # Verify that a non-organizer user does not see the countdown for a past event
        self.client.login(username=self.regular_user.username, password="password123")
        response = self.client.get(f'/events/{self.past_event.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Cuenta Regresiva')  
        self.assertFalse(response.context["user_is_organizer"])

    def test_past_event_detail_shows_buy_button_for_non_organizer(self):
        # Verify that a non-organizer user sees the buy button for a past event
        self.client.login(username=self.regular_user.username, password="password123")
        response = self.client.get(f'/events/{self.past_event.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Comprar')  
        self.assertFalse(response.context["user_is_organizer"])

    def test_past_event_detail_dont_shows_buy_button_for_non_organizer(self):
        # Verify that a non-organizer user sees the buy button for a future event
        self.client.login(username=self.regular_user.username, password="password123")
        response = self.client.get(f'/events/{self.future_event.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Comprar')  
        self.assertFalse(response.context["user_is_organizer"])

    def test_past_event_detail_shows_message_for_non_organizer(self):
        # Verify that a non-organizer user sees the message indicating the event has passed
        self.client.login(username=self.regular_user.username, password="password123")
        response = self.client.get(f'/events/{self.past_event.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Este concierto ya pasó') 
        self.assertFalse(response.context["user_is_organizer"]) 

    def test_event_detail_dont_shows_countdown_for_organizer(self):
        # Verify that the organizer does not see the countdown
        self.client.login(username=self.organizer.username, password="password123")
        response = self.client.get(f'/events/{self.future_event.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Cuenta Regresiva') 
        self.assertTrue(response.context["user_is_organizer"])
    
    def test_event_detail_dont_shows_message_for_organizer(self):
        # Verify that the organizer does not see the "event passed" message
        self.client.login(username=self.organizer.username, password="password123")
        response = self.client.get(f'/events/{self.past_event.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Este concierto ya pasó')
        self.assertTrue(response.context["user_is_organizer"])