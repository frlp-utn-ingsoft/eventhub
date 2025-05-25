from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from app.models import Event, Venue, User
from datetime import timedelta
from app.test.test_e2e.base import BaseE2ETest
from playwright.sync_api import expect

class EventVisibilityTests(BaseE2ETest):
    def setUp(self):
        super().setUp()

        # Create regular user
        self.regular_user = User.objects.create_user(
            username="regular",
            email="regular@test.com",
            password="password123",
            is_organizer=False,
        )

        # Create organizer user
        self.organizer_user = User.objects.create_user(
            username="organizer",
            email="organizer@test.com",
            password="password123",
            is_organizer=True,
        )

        # Create a venue
        self.venue = Venue.objects.create(
            name="National Auditorium",
            address="60 y 124",
            capacity=5000,
            country="ARG",
            city="La Plata"
        )

        # Past event
        self.past_event = Event.objects.create(
            title="Past Event",
            description="Event that already happened",
            scheduled_at=timezone.now() - timedelta(days=2),
            organizer=self.organizer_user,
            venue=self.venue
        )

        # Future event
        self.future_event = Event.objects.create(
            title="Future Event",
            description="Event that has not occurred yet",
            scheduled_at=timezone.now() + timedelta(days=2),
            organizer=self.organizer_user,
            venue=self.venue
        )

    def test_do_not_show_buy_button_for_past_event(self):
        self.login_user("regular", "password123")
        self.page.goto(f"{self.live_server_url}/events/{self.past_event.id}/")
        buy_link = self.page.get_by_role("link", name="Comprar")
        expect(buy_link).to_have_count(0)

    def test_show_buy_button_for_future_event(self):
        self.login_user("regular", "password123")
        self.page.goto(f"{self.live_server_url}/events/{self.future_event.id}/")
        buy_link = self.page.get_by_role("link", name="Comprar")
        expect(buy_link).to_be_visible()

    def test_countdown_section_visible_for_non_organizer(self):
        # Login as non-organizer user
        self.login_user('regular', "password123")
        self.page.goto(f"{self.live_server_url}/events/{self.future_event.id}/")
        # Verify countdown section is present
        countdown_section = self.page.locator('.countdown-section')
        expect(countdown_section).to_be_visible()

    def test_countdown_section_not_visible_for_organizer(self):
        # Login as organizer
        self.login_user('organizador', "password123")
        self.page.goto(f"{self.live_server_url}/events/{self.future_event.id}/")
        # Verify countdown section is not present
        countdown_section = self.page.locator('.countdown-section')
        expect(countdown_section).to_have_count(0)