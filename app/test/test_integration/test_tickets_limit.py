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
                },
                follow=True
            )
            self.assertEqual(response.status_code, 200)
            self.event.refresh_from_db()  # Actualizar datos del evento

    # Verificar disponibilidad exacta
        self.event.refresh_from_db()
        self.assertEqual(self.event.tickets_available, 0, 
                        f"Deberían haber 0 tickets disponibles, pero hay {self.event.tickets_available}")

    # Intentar comprar un ticket más
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
            },
            follow=True
        )
    
    # Verificar que no se permitió la compra
        self.assertContains(response, "No hay suficientes tickets disponibles", status_code=200)
        self.event.refresh_from_db()
        self.assertEqual(self.event.tickets_available, 0, 
                        "La disponibilidad no debería cambiar después de intentar comprar sin stock")