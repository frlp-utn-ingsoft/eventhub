from django.test import TestCase
from django.utils import timezone

from app.models import Event, User
from tickets.forms import TicketCompraForm, TicketUpdateForm
from tickets.models import Ticket


class TicketCompraFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='usuario1',
            email='user@example.com',
            password='password123'
        )
        self.event = Event.objects.create(
            title='Evento Test',
            description='Evento de prueba',
            scheduled_at=timezone.now() + timezone.timedelta(days=5),
            organizer=self.user
        )

    def test_form_valido_con_3_tickets(self):
        form = TicketCompraForm(
            data={'type': 'General', 'quantity': 3},
            user=self.user,
            event=self.event
        )
        self.assertTrue(form.is_valid())

    def test_form_invalido_con_5_tickets(self):
        form = TicketCompraForm(
            data={'type': 'General', 'quantity': 5},
            user=self.user,
            event=self.event
        )
        self.assertFalse(form.is_valid())
        self.assertIn('No se pueden comprar más de 4 tickets', str(form.errors))

class TicketUpdateFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='usuario1',
            email='user@example.com',
            password='password123'
        )
        self.event = Event.objects.create(
            title='Evento Test',
            description='Evento de prueba',
            scheduled_at=timezone.now() + timezone.timedelta(days=5),
            organizer=self.user
        )

    def test_update_form_valido_con_cantidad_permitida(self):
        ticket = Ticket.objects.create(user=self.user, event=self.event, quantity=2)
        
        form = TicketUpdateForm(
            data={'type': 'VIP', 'quantity': 3},
            user=self.user,
            event=self.event,
            ticket_instance=ticket
        )
        self.assertTrue(form.is_valid())

    def test_update_form_invalido_si_supera_limite_total(self):
        ticket1 = Ticket.objects.create(user=self.user, event=self.event, quantity=2)
        
        form = TicketUpdateForm(
            data={'type': 'General', 'quantity': 5},
            user=self.user,
            event=self.event,
            ticket_instance=ticket1
        )
        self.assertFalse(form.is_valid())
        self.assertIn('No se pueden tener más de 4 tickets', str(form.errors))
