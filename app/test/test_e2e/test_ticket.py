from django.test import TestCase
from django.utils import timezone

from app.models import Event, Ticket, User


class TicketLimitUnitTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user1", password="pass")
        self.organizer = User.objects.create_user(username="org1", password="pass", is_organizer=True)
        self.event = Event.objects.create(
            title="Evento Test",
            description="Test",
            scheduled_at=timezone.now() + timezone.timedelta(days=2),
            organizer=self.organizer
        )

    def test_user_cannot_purchase_more_than_5_tickets(self):
        """Verifica que un usuario no pueda superar los 5 tickets por evento"""
        # Crear 3 tickets primero
        Ticket.new(user=self.user, event=self.event, quantity=3, ttype="GENERAL")
        # Intentar crear 3 más (total = 6)
        success, _ = Ticket.new(user=self.user, event=self.event, quantity=3, ttype="GENERAL")
        self.assertFalse(success)
