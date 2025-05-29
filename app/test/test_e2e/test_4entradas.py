from app.test.test_e2e.base import BaseE2ETest 
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.urls import reverse
from django.test import TestCase
from app.models import Event, Ticket, User
from django.utils import timezone
from decimal import Decimal
import pytest
from app.forms import TicketForm
from django.contrib.auth import get_user_model
import datetime

class EditarTicketE2ETest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="e2euser",
            email="e2euser@test.com",
            password="e2epass",
            is_organizer=True,
        )
        self.event = Event.objects.create(
            title="Evento E2E",
            description="Desc",
            scheduled_at=timezone.now() + timezone.timedelta(days=5),
            organizer=self.user,
            price_general=Decimal("50.00"),
            price_vip=Decimal("100.00")
        )
        self.client.login(username='e2euser', password='e2epass')
        # Ticket original con 2 entradas
        self.ticket = Ticket.objects.create(user=self.user, event=self.event, quantity=2, type='general',card_type='debit')

        # Otro ticket para sumar hasta 4
        Ticket.objects.create(user=self.user, event=self.event, quantity=2, type='vip')

    def test_no_puede_editar_ticket_si_supera_maximo(self):
        response = self.client.post(reverse('update_ticket', args=[self.ticket.ticket_code]), {
            'event': self.event.id,
            'quantity': 3,
            'type': 'general',
        })
        self.assertContains(response, "No podés comprar más de 4 entradas")
