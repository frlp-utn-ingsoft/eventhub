from django.test import TestCase
from django.utils import timezone
from app.models import Refund, Ticket, User, Event

class RefundModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user1", email="user1@example.com", password="pass123"
        )
        self.organizer = User.objects.create_user(
            username="org1", email="org1@example.com", password="pass123", is_organizer=True
        )
        event_date = timezone.now() + timezone.timedelta(days=1)
        self.event = Event.objects.create(
            title="E1", description="Desc", scheduled_at=event_date, organizer=self.organizer
        )
        self.ticket = Ticket.objects.create(
            user=self.user, event=self.event, quantity=1, type="GENERAL"
        )

    def test_get_status_display_pending(self):
        refund = Refund(ticket_code=self.ticket.ticket_code, reason="r", user=self.user, event=self.event)
        self.assertEqual(refund.get_status_display(), "Pendiente")

    def test_get_status_display_approved(self):
        refund = Refund.objects.create(
            ticket_code=self.ticket.ticket_code, reason="r", user=self.user, event=self.event, approved=True
        )
        self.assertEqual(refund.get_status_display(), "Aprobado")

    def test_get_status_display_rejected(self):
        refund = Refund.objects.create(
            ticket_code=self.ticket.ticket_code, reason="r", user=self.user, event=self.event, approved=False
        )
        self.assertEqual(refund.get_status_display(), "Rechazado")

    def test_validate_empty_reason(self):
        refund = Refund(ticket_code=self.ticket.ticket_code, reason="  ", user=self.user, event=self.event)
        errors = refund.validate()
        self.assertIn("reason", errors)

    def test_validate_duplicate_pending(self):
        Refund.objects.create(
            ticket_code=self.ticket.ticket_code, reason="r1", user=self.user, event=self.event
        )
        refund2 = Refund(ticket_code=self.ticket.ticket_code, reason="r2", user=self.user, event=self.event)
        errors = refund2.validate()
        self.assertIn("__all__", errors)