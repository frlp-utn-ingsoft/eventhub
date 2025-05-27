from django.test import TestCase
from django.utils import timezone
from app.models import Event, Venue, User  # Ajusta imports según tu estructura
import datetime

class EventStateUnitTest(TestCase):

    def setUp(self):
        self.organizer = User.objects.create_user(username="organizer", password="pass")
        self.venue = Venue.objects.create(name="Test Venue", capacity=100)

    def test_default_state_is_active(self):
        event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
        )
        self.assertEqual(event.state, Event.ACTIVE)

    def test_update_event_sets_reprogramed_if_date_changes(self):
        event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
        )
        new_date = timezone.now() + datetime.timedelta(days=5)
        event.update(scheduled_at=new_date)
        self.assertEqual(event.state, Event.REPROGRAMED)

    def test_auto_update_state_sets_finished_if_date_passed(self):
        past_date = timezone.now() - datetime.timedelta(days=1)
        event = Event.objects.create(
            title="Past Event",
            description="Test Description",
            scheduled_at=past_date,
            organizer=self.organizer,
            venue=self.venue,
        )
        event.auto_update_state()
        self.assertEqual(event.state, Event.FINISHED)

    def test_auto_update_state_sets_sold_out_if_no_tickets_available(self):
        event = Event.objects.create(
            title="Sold Out Event",
            description="Test Description",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
        )
        # Simulamos que no hay tickets disponibles, seteamos a 0
        def fake_available_tickets():
            return 0
        event.available_tickets = fake_available_tickets
        event.auto_update_state()
        self.assertEqual(event.state, Event.SOLD_OUT)
