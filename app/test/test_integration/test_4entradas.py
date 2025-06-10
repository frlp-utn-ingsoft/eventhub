from django.urls import reverse
from django.test import TestCase
from app.models import Event, Ticket, User
from django.utils import timezone
from decimal import Decimal
import pytest
from app.forms import TicketForm
from django.contrib.auth import get_user_model
import datetime

class ComprarTicketIntegrationTest(TestCase):

    def setUp(self):
        # Crear usuario organizador
        self.user = User.objects.create_user(
            username="org",
            email="org@test.com",
            password="password123",
            is_organizer=True,
        )
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.user,
            price_general=Decimal('100.00'),
            price_vip=Decimal('200.00')
        )
        self.client.login(username='org', password='password123')
        Ticket.objects.create(user=self.user,
                              event=self.event,
                              quantity=4, 
                              type='general', 
                              card_type='debit')

    def test_no_puede_comprar_si_ya_tiene_4(self):
        response = self.client.post(reverse('buy_ticket'), {
            'event': self.event.id,
            'quantity': 1,
            'type': 'general',
            'card_type': 'debit',
            'card_number': '1234567812345678',
            'card_cvv': '123',
            'expiry_month': '12',
            'expiry_year': '2035',
        })
        self.assertContains(response, "No pueden comprarse más de 4 entradas")
