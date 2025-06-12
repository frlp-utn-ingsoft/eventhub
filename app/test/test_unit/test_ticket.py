from datetime import datetime, timedelta, timezone

from django.test import TestCase

from app.models import Event, Ticket, User, Venue


class TicketValidationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="1234")
        self.venue = Venue.objects.create(
            name="Test Venue", address="Test St", city="Test City", capacity=100,
            contact_info="info@test.com", created_by=self.user
        )
        self.event = Event.objects.create(
            title="Evento Test",
            description="Descripción de prueba",
            scheduled_at=datetime.now() + timedelta(days=5),
            organizer=self.user,
            venue=self.venue,
            status="activo",
            available_tickets=100
        )

    def test_cantidad_valida(self):
        valido, mensaje = Ticket.validate_ticket_purchase(self.event, 3, self.user)
        self.assertTrue(valido)
        self.assertEqual(mensaje, None)

    def test_exceso_de_tickets(self):
        Ticket.objects.create(user=self.user, event=self.event, quantity=3, type="GENERAL", price_paid=150)
        valido, mensaje = Ticket.validate_ticket_purchase(self.event, 2, self.user) 
        self.assertFalse(valido)
        self.assertIn("No puedes comprar más de", mensaje)
