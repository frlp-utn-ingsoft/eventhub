from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from app.models import Event, Venue, Category
from django.contrib.auth import get_user_model
User = get_user_model()
import datetime

class EventStateIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='organizer', password='testpass', is_organizer=True)
        self.venue = Venue.objects.create(name="Test Venue", adress="Test Adress", capacity=100)
        self.category = Category.objects.create(name="Music", is_active=True)

        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            organizer=self.user,
            venue=self.venue
        )
        self.event.categories.add(self.category)  # Relación M2M

        self.event_id = self.event.id  # Se accede después de crear
        self.venue_id = self.venue.id

        self.client.login(username='organizer', password='testpass')

    def test_event_reprograms_when_date_changes(self):
        new_date = (timezone.now() + datetime.timedelta(days=5)).date().strftime('%Y-%m-%d')
        new_time = '15:00'

        response = self.client.post(reverse('event_edit', args=[self.event_id]), {
            'title': self.event.title,
            'description': self.event.description,
            'date': new_date,
            'time': new_time,
            'venue': str(self.venue_id),
            'categories': [self.category.id]
        })

        self.event.refresh_from_db()
        self.assertEqual(self.event.state, Event.REPROGRAMED)

    def test_event_canceled_view_sets_state_correctly(self):
        response = self.client.post(reverse('event_canceled', args=[self.event_id]))
        self.event.refresh_from_db()
        self.assertEqual(self.event.state, Event.CANCELED)
