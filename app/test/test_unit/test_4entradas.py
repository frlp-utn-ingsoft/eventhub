# tests/test_forms.py

import pytest
from app.forms import TicketForm
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
import datetime
from decimal import Decimal
from app.models import Event, User, Ticket


class TicketFormUnitTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="organizador",
            email="user@test.com",
            password="password123",
            is_organizer=True,
        )
        self.event = Event.objects.create(
            title="Evento Test",
            description="Descripción",
            scheduled_at=timezone.now() + timezone.timedelta(days=10),
            organizer=self.user,
            price_general=Decimal("100.00"),
            price_vip=Decimal("200.00")
        )
        # Usuario ya tiene 3 entradas
        Ticket.objects.create(user=self.user, event=self.event, quantity=3, type='general', card_type='credit')

    def test_no_puede_comprar_mas_de_4(self):
        form_data = {
            'event': self.event.id,
            'quantity': 2,
            'type': 'vip',
            'card_type': 'credit',
            'card_number': '1234567812345678',
            'card_cvv': '123',
            'expiry_month': '12',
            'expiry_year': '30'
        }
        form = TicketForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
