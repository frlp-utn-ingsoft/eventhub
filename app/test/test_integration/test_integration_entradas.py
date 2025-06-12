from django.test import TestCase
from app.models import Event, Ticket, User, Venue
from datetime import datetime, timedelta

class EventIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='organizer', password='test123')
        self.venue = Venue.objects.create(
            name="Venue Integración", address="Calle Falsa 123", city="Springfield", capacity=200, contact_info="email@test.com", created_by=self.user
        )
        self.event = Event.objects.create(
            title="Evento Integración",
            description="Descripción",
            scheduled_at=datetime.now() + timedelta(days=5),
            organizer=self.user,
            venue=self.venue
        )

    def test_event_with_tickets_integration(self):
        Ticket.objects.create(user=self.user, event=self.event, quantity=100, price_paid=50)
        Ticket.objects.create(user=self.user, event=self.event, quantity=50, price_paid=75)

        self.assertEqual(self.event.entradas_vendidas(), 150)
        self.assertEqual(round(self.event.porcentaje_ocupacion(), 2), 75.00)
        self.assertEqual(self.event.estado_demanda(), "")