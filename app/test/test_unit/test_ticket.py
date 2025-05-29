from django.db.models import Sum
from django.test import TestCase
from django.utils import timezone

from app.models import Event, Ticket, User, Venue


class TicketLimitUnitTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user1", password="pass")
        self.organizer = User.objects.create_user(
            username="org1", password="pass", is_organizer=True
        )
        venue = Venue.objects.create(
            name="Venue Test", address="123 Test St", city="Test City", capacity=5
        )
        self.event = Event.objects.create(
            venue=venue,
            title="Evento Test",
            description="Test",
            scheduled_at=timezone.now() + timezone.timedelta(days=2),
            organizer=self.organizer,
        )

    def test_user_cannot_purchase_more_than_4_tickets(self):
        """Verifica que un usuario no pueda superar los 4 tickets por evento"""
        # Crear 3 tickets primero
        success, result = Ticket.new(
            user=self.user, event=self.event, quantity=3, ticket_type="GENERAL"
        )
        self.assertTrue(success, "Initial ticket creation should succeed")

        # Intentar comprar 3 más excediendo las 4 entradas
        success, errors = Ticket.new(
            user=self.user, event=self.event, quantity=3, ticket_type="GENERAL"
        )
        self.assertFalse(success, "Should fail when exceeding 4 tickets")
        self.assertIn("quantity", errors, "Error should indicate quantity issue")
        self.assertEqual(
            errors["quantity"],
            "No puedes comprar más de 4 entradas por evento.",
            "Error message should match",
        )

    def test_user_cannot_purchase_tickets_exceeding_event_capacity(self):
        """Verifica que un usuario no pueda comprar ticket para un evento excedido de su capacidad"""

        # Otro usuario compra 3 tickets primero
        user2 = User.objects.create_user(username="user2", password="12345678", is_organizer=False)

        success, result = Ticket.new(
            user=user2, event=self.event, quantity=3, ticket_type="GENERAL"
        )

        self.assertTrue(success, "Initial ticket creation should succeed")

        # El usuario intenta comprar 4 tickets excediendo capacidad del evento (3 + 4 < 6)
        success, errors = Ticket.new(
            user=self.user, event=self.event, quantity=4, ticket_type="GENERAL"
        )

        self.assertFalse(success, "Should fail when exceeding event capacity")
        self.assertIn("capacity", errors, "Error should indicate capacity issue")
        self.assertEqual(
            errors["capacity"],
            "No puedes comprar más tickets que la capacidad del evento",
            "Error message should match",
        )
