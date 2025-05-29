import datetime
from django.test import TestCase
from django.utils import timezone
from app.models import Event, User, Ticket, Venue

class EventGetDemandTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True
        )
        self.venue = Venue.objects.create(
            name="Test Venue",
            adress="Test Address",
            city="Test City",
            capacity=100,
            contact="Test Contact"
        )

    def test_event_get_demand(self):
        """Test que verifica el cálculo correcto de la demanda del evento"""
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue
        )

        # Sin tickets: demanda debe ser 0%
        self.assertEqual(event.get_demand(), 0)

        # Creamos 50 tickets (capacidad 100)
        for i in range(50):
            user = User.objects.create_user(
                username=f"user_{i}",
                email=f"user_{i}@test.com",
                password="password123"
            )
            Ticket.objects.create(
                user=user,
                event=event,
                type="general",
                quantity=1
            )

        # Demanda debe ser 50%
        self.assertEqual(event.get_demand(), 50)

        # Creamos 50 tickets más (total 100)
        for i in range(50, 100):
            user = User.objects.create_user(
                username=f"user_{i}",
                email=f"user_{i}@test.com",
                password="password123"
            )
            Ticket.objects.create(
                user=user,
                event=event,
                type="general",
                quantity=1
            )

        # Demanda debe ser 100%
        self.assertEqual(event.get_demand(), 100)