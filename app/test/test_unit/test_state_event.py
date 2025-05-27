from django.test import TestCase
from app.models import User
from app.models import Event, Venue
from django.utils.timezone import make_aware
from datetime import datetime

class EventModelUnitTest(TestCase):
    def setUp(self):
        # Crear usuario y venue para el evento
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.venue = Venue.objects.create(
            name="Venue Test",
            address="Calle Falsa 123",
            city="Ciudad Test",
            capacity=100,
            contact="contacto@test.com"
        )
    
    def test_event_status_default_active(self):
        # Crear evento sin especificar status, debe tomar 'active' por defecto
        event = Event.objects.create(
            title="Evento Test",
            description="Descripción test",
            scheduled_at=make_aware(datetime(2025, 6, 30, 18, 0, 0)),
            organizer=self.user,
            venue=self.venue
            # no le pasamos status, debe tomar el default 'active'
        )
        self.assertEqual(event.status, 'active')
