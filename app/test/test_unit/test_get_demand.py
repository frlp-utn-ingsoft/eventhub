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
            capacity=10, ##capacidad de 10
            contact="Test Contact"
        )
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue
        )
        self.user1 = User.objects.create_user(
            username="usuario",
            password="password123",
            is_organizer=False
        )
        self.user2 = User.objects.create_user(
            username="usuario2",
            password="password123",
            is_organizer=False  
        )

    def test_event_get_demand(self):
        """Test que verifica el cálculo correcto de la demanda del evento"""

        # Sin tickets: demanda debe ser 0%
        self.assertEqual(self.event.get_demand(), 0)
        #Creamos dos ticket para el evento
        Ticket.objects.create(
                user=self.user1,
                event=self.event,
                type="general",
                quantity=1
            )
        Ticket.objects.create(
                user=self.user2,
                event=self.event,
                type="general",
                quantity=1
            )
        
        # Demanda debe ser 20%
        self.assertEqual(self.event.get_demand(), 20)
       
        