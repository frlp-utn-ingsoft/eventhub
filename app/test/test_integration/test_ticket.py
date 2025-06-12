from django.test import TestCase
from django.urls import reverse
from app.models import User, Event, Ticket, Venue
from datetime import datetime, timedelta
from django.utils import timezone

class TicketPurchaseIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="integrationuser", password="1234")
        self.client.login(username="integrationuser", password="1234")
        self.venue = Venue.objects.create(
            name="Venue Test", address="Calle Falsa 123", city="Ciudad", capacity=100,
            contact_info="contacto@ejemplo.com", created_by=self.user
        )
        self.event = Event.objects.create(
            title="Evento Integración",
            description="Test de integración",
            scheduled_at=timezone.now() + timedelta(days=7),
            organizer=self.user,
            venue=self.venue,
            available_tickets=10 
        )

    def test_compra_valida(self):
        response = self.client.post(reverse('ticket_form'), {
            'event': self.event.id,
            'type': 'GENERAL',
            'quantity': 2
        })
        self.assertEqual(response.status_code, 302)  # Redirige correctamente
        self.assertEqual(Ticket.objects.count(), 1)

    def test_compra_invalida_supera_limite(self):
        Ticket.objects.create(user=self.user, event=self.event, quantity=3, type="GENERAL", price_paid=150)
        response = self.client.post(reverse('ticket_form'), {
            'event': self.event.id,
            'type': 'GENERAL',
            'quantity': 2
        })
        self.assertEqual(response.status_code, 200)  # No redirige
        self.assertContains(response, "No puedes comprar más de")