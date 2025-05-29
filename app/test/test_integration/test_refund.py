from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
import datetime

from app.models import Refund, Ticket, User, Event

class RefundViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="regular", email="u@example.com", password="pass123"
        )
        self.organizer = User.objects.create_user(
            username="organizer", email="o@example.com", password="pass123", is_organizer=True
        )
        event_date = timezone.now() + timezone.timedelta(days=1)
        self.event = Event.objects.create(
            title="E", description="Desc", scheduled_at=event_date, organizer=self.organizer
        )
        self.ticket = Ticket.objects.create(
            user=self.user, event=self.event, quantity=1, type="VIP"
        )

    def test_refund_create_requires_login(self):
        # Si no estás logueado, GET app/refund/create/ redirige al login
        response = self.client.get(reverse('refund_create'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith('/accounts/login/'))

    def test_refund_create_get_with_login(self):
        # Si estás logueado, GET muestra el formulario
        self.client.login(username="regular", password="pass123")
        response = self.client.get(reverse('refund_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/refund/refund_form.html')
        # El contexto debe contener los tickets del usuario
        self.assertIn('user_tickets', response.context)
        self.assertIn(self.ticket, response.context['user_tickets'])

    def test_refund_create_post_success(self):
        self.client.login(username="regular", password="pass123")
        response = self.client.post(
            reverse('refund_create'),
            {'ticket_code': self.ticket.ticket_code, 'reason': 'motivo'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Refund.objects.filter(user=self.user, ticket_code=self.ticket.ticket_code).exists())

    def test_refund_create_post_duplicate(self):
        self.client.login(username="regular", password="pass123")
        Refund.objects.create(ticket_code=self.ticket.ticket_code, reason="r", user=self.user, event=self.event)
        response = self.client.post(
            reverse('refund_create'),
            {'ticket_code': self.ticket.ticket_code, 'reason': 'otra'},
        )
        self.assertContains(response, 'Ya tienes una solicitud de reembolso pendiente')
        
    def test_refund_edit_requires_login(self):
        refund =Refund.objects.create(ticket_code=self.ticket.ticket_code, reason="r", user=self.user, event=self.event)
        response = self.client.get(reverse('refund_edit', args=[refund.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith('/accounts/login/'))
        
    def test_refund_approve_status_change(self):
        self.client.login(username="organizer", password="pass123")
        refund = Refund.objects.create(ticket_code=self.ticket.ticket_code, reason="r", user=self.user, event=self.event)
        response = self.client.post(reverse('refund_approve', args=[refund.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        refund.refresh_from_db()
        self.assertEqual(refund.get_status_display(), "Aprobado")
        self.assertTrue(refund.approved)
        
        

    