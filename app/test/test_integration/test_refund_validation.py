from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
import datetime

from app.models import User, Event, Venue, Category, Ticket, RefundRequest

class RefundValidationIntegrationTest(TestCase):
    """Tests de integración para la validación de solicitudes de reembolso"""

    def setUp(self):
        self.client = Client()
        
        # Crear usuario
        self.user = User.objects.create_user(
            username="usuario_test",
            email="usuario@test.com",
            password="password123"
        )

        # Crear venue y categoría
        self.venue = Venue.objects.create(
            name="Venue de prueba",
            adress="Dirección de prueba",
            city="Ciudad de prueba",
            capacity=100,
            contact="contacto@prueba.com"
        )

        self.category = Category.objects.create(
            name="Categoría de prueba",
            description="Descripción de la categoría de prueba",
            is_active=True
        )

        # Crear evento
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.user,
            venue=self.venue,
            category=self.category
        )

        # Crear ticket
        self.ticket = Ticket.objects.create(
            user=self.user,
            event=self.event,
            quantity=1,
            type="REGULAR"
        )

        # Iniciar sesión
        self.client.login(username="usuario_test", password="password123")

    def test_cannot_create_refund_with_active_request(self):
        """Test que verifica que no se puede crear una solicitud si ya hay una activa"""
        # Crear primera solicitud
        RefundRequest.objects.create(
            user=self.user,
            ticket_code=self.ticket.ticket_code,
            reason="Razón de prueba 1",
            event_name=self.event.title
        )

        # Intentar crear segunda solicitud
        response = self.client.post(
            reverse('refund_form', args=[self.ticket.id]),
            {
                'ticket_code': self.ticket.ticket_code,
                'reason': 'Razón de prueba 2',
                'accepted_policy': 'on'
            }
        )

        # Verificar que se redirige con mensaje de error
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)

    def test_can_create_refund_after_rejected(self):
        """Test que verifica que se puede crear una solicitud después de que una fue rechazada"""
        # Crear y rechazar primera solicitud
        refund1 = RefundRequest.objects.create(
            user=self.user,
            ticket_code=self.ticket.ticket_code,
            reason="Razón de prueba 1",
            event_name=self.event.title
        )
        refund1.approval = False
        refund1.save()

        # Crear segunda solicitud
        response = self.client.post(
            reverse('refund_form', args=[self.ticket.id]),
            {
                'ticket_code': self.ticket.ticket_code,
                'reason': 'Razón de prueba 2',
                'accepted_policy': 'on'
            }
        )

        # Verificar que se creó la solicitud
        self.assertEqual(response.status_code, 302)
        self.assertTrue(RefundRequest.objects.filter(reason='Razón de prueba 2').exists())

    def test_can_create_refund_after_approved(self):
        """Test que verifica que se puede crear una solicitud después de que una fue aprobada"""
        # Crear y aprobar primera solicitud
        refund1 = RefundRequest.objects.create(
            user=self.user,
            ticket_code=self.ticket.ticket_code,
            reason="Razón de prueba 1",
            event_name=self.event.title
        )
        refund1.approval = True
        refund1.save()

        # Crear segunda solicitud
        response = self.client.post(
            reverse('refund_form', args=[self.ticket.id]),
            {
                'ticket_code': self.ticket.ticket_code,
                'reason': 'Razón de prueba 2',
                'accepted_policy': 'on'
            }
        )

        # Verificar que se creó la solicitud
        self.assertEqual(response.status_code, 302)
        self.assertTrue(RefundRequest.objects.filter(reason='Razón de prueba 2').exists()) 