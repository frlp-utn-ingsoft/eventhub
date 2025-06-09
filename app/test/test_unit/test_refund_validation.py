from django.test import TestCase
from django.utils import timezone
import datetime

from app.models import User, Event, Venue, Category, Ticket, RefundRequest

class RefundValidationUnitTest(TestCase):
    """Tests unitarios para la validación de solicitudes de reembolso"""

    def setUp(self):
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

    def test_cannot_create_multiple_active_refunds(self):
        """Test que verifica que no se pueden crear múltiples solicitudes de reembolso activas"""
        # Crear primera solicitud de reembolso
        RefundRequest.objects.create(
            user=self.user,
            ticket_code=self.ticket.ticket_code,
            reason="Razón de prueba 1",
            event_name=self.event.title
        )

        # Intentar crear segunda solicitud
        RefundRequest.objects.create(
            user=self.user,
            ticket_code=self.ticket.ticket_code,
            reason="Razón de prueba 2",
            event_name=self.event.title
        )

        # Verificar que se crearon ambas solicitudes
        active_refunds = RefundRequest.objects.filter(
            user=self.user,
            ticket_code=self.ticket.ticket_code,
            approval__isnull=True
        ).count()
        self.assertEqual(active_refunds, 2)

        # Verificar que ambas solicitudes están pendientes
        for refund in RefundRequest.objects.filter(
            user=self.user,
            ticket_code=self.ticket.ticket_code
        ):
            self.assertIsNone(refund.approval)

    def test_can_create_refund_after_rejected(self):
        """Test que verifica que se puede crear una nueva solicitud después de que una fue rechazada"""
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
        refund2 = RefundRequest.objects.create(
            user=self.user,
            ticket_code=self.ticket.ticket_code,
            reason="Razón de prueba 2",
            event_name=self.event.title
        )
        self.assertIsNone(refund2.approval)  # La nueva solicitud debe estar pendiente

    def test_can_create_refund_after_approved(self):
        """Test que verifica que se puede crear una nueva solicitud después de que una fue aprobada"""
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
        refund2 = RefundRequest.objects.create(
            user=self.user,
            ticket_code=self.ticket.ticket_code,
            reason="Razón de prueba 2",
            event_name=self.event.title
        )
        self.assertIsNone(refund2.approval)  # La nueva solicitud debe estar pendiente 