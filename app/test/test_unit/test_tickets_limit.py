from django.core.exceptions import ValidationError
from django.test import TestCase
from app.models import Event, Ticket, User, Location
from app.forms import TicketForm
from decimal import Decimal
import datetime
from django.utils import timezone

class TicketsLimitTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )
        self.location = Location.objects.create(
            name="Sala Principal",
            address="Calle Principal 123",
            city="Ciudad",
            capacity=10
        )
        self.event = Event.objects.create(
            title="Evento Test",
            description="Test",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            location=self.location,
            tickets_total=5,
            price_general=Decimal('100.00'),
            price_vip=Decimal('200.00')
        )

    def test_tickets_limit(self):
        """Test que verifica que no se pueden comprar más tickets que los disponibles"""
        # Vender todos los tickets disponibles
        for _ in range(self.event.tickets_total):
            Ticket.objects.create(
                event=self.event,
                type='general',
                quantity=1,
                card_type='credit',
                user=self.organizer
            )

        self.event.refresh_from_db()
        self.assertEqual(self.event.tickets_available, 0)

        data = {
            'event': self.event.id,
            'type': 'general',
            'quantity': 1,
            'card_number': '1234567812345678',
            'card_cvv': '123',
            'card_type': 'credit',
            'expiry_month': '12',
            'expiry_year': '30'
        }
        form = TicketForm(data, fixed_event=True, event_instance=self.event)
        self.assertFalse(form.is_valid())
        self.assertIn('quantity', form.errors)