from django.test import TestCase, Client
from django.urls import reverse
from app.models import Event, User, Location
from decimal import Decimal
import datetime
from django.utils import timezone

class TicketsLimitIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )
        self.user = User.objects.create_user(
            username="comprador",
            email="comprador@test.com",
            password="password123",
            is_organizer=False,
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
            tickets_total=2,
            price_general=Decimal('100.00'),
            price_vip=Decimal('200.00')
        )

    def test_tickets_limit(self):
        self.client.login(username="comprador", password="password123")

        # Comprar todos los tickets disponibles
        for _ in range(self.event.tickets_total):
            response = self.client.post(
                reverse("buy_ticket_from_event", args=[self.event.id]),
                {
                    'type': 'general',
                    'quantity': 1,
                    'card_number': '1234567812345678',
                    'card_cvv': '123',
                    'card_type': 'credit',
                    'expiry_month': '12',
                    'expiry_year': '30'
                }
            )
            self.assertNotContains(response, "Solo hay 0 tickets disponibles para este evento.")

        # Intentar comprar un ticket mas
        response = self.client.post(
            reverse("buy_ticket_from_event", args=[self.event.id]),
            {
                'type': 'general',
                'quantity': 1,
                'card_number': '1234567812345678',
                'card_cvv': '123',
                'card_type': 'credit',
                'expiry_month': '12',
                'expiry_year': '30'
            }
        )
        self.assertContains(response, "Solo hay 0 tickets disponibles para este evento.")