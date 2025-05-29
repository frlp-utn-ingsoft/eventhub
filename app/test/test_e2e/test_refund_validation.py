# app/test/test_e2e/test_refund_validation.py
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client, TestCase
# Asegúrate de importar todos los modelos necesarios
from app.models import Event, User, Ticket, RefundRequest, Venue, Category, Notification 
from django.utils import timezone
from datetime import timedelta
import datetime
import uuid # Necesario porque ticket_code es un UUIDField
from unittest.mock import patch # <-- Importar patch para mockear

User = get_user_model()

class RefundRequestValidationTests(TestCase):
    def setUp(self):
        # Crear un organizador y un usuario comprador
        self.organizer = User.objects.create_user(
            username='organizer_e2e', email='organizer_e2e@example.com', password='password', is_organizer=True
        )
        self.buyer = User.objects.create_user(
            username='buyer_e2e', email='buyer_e2e@example.com', password='password', is_organizer=False
        )

        # Crear un lugar
        self.venue = Venue.objects.create(
            name='Test Venue E2E', adress='123 E2E St', city='E2E City', capacity=10, contact='e2e@venue.com'
        )
        
        # Crear una categoría
        self.category = Category.objects.create(name='E2E Category', description='E2E Desc')

        # Crear un evento, asignando la categoría directamente (ForeignKey)
        self.event = Event.objects.create(
            title='Concierto Test E2E',
            description='Un concierto para pruebas E2E de reembolso',
            scheduled_at=timezone.make_aware(datetime.datetime(2025, 12, 31, 20, 0, 0)),
            organizer=self.organizer,
            venue=self.venue,
            state=Event.ACTIVE,
            category=self.category # Asignación directa de ForeignKey
        )

        # Crear un ticket para el comprador
        self.ticket = Ticket.objects.create(
            event=self.event,
            user=self.buyer,
            type=Ticket.GENERAL,
            quantity=1,
        )
        # Recupera el ticket_code generado como string para usarlo en los datos POST y RefundRequest
        self.ticket_code_str = str(self.ticket.ticket_code)

        self.client = Client()

    # Usamos @patch para mockear la creación de Notification.objects.create
    # Esto evitará el TypeError, ya que no intentaremos crear la notificación de verdad.
    # El path debe ser donde Notification.objects.create es *llamado*, que es en app.views
    @patch('app.views.Notification.objects.create')
    def test_user_can_submit_refund_request_successfully(self, mock_notification_create):
        """
        Test 1: Un usuario puede enviar una solicitud de reembolso exitosamente para un ticket.
        La notificación se mockea para evitar errores ajenos al test de reembolso.
        """
        self.client.force_login(self.buyer)
        url = reverse("refund_form", kwargs={"id": self.ticket.id})

        data = {
            "ticket_code": self.ticket_code_str,
            "reason": "Cambio de planes en E2E",
            "additional_details": "No podré asistir al evento E2E.",
            "accepted_policy": "on"
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("tickets"))

        refund_request = RefundRequest.objects.get(ticket_code=self.ticket_code_str)
        self.assertIsNotNone(refund_request)
        self.assertEqual(refund_request.user, self.buyer)
        self.assertEqual(refund_request.reason, "Cambio de planes en E2E")
        self.assertIsNone(refund_request.approval)

        # Verificamos que mock_notification_create fue llamado
        mock_notification_create.assert_called_once()


    @patch('app.views.Notification.objects.create')
    def test_user_cannot_submit_duplicate_refund_request_for_same_ticket(self, mock_notification_create):
        """
        Test 2: Un usuario no puede enviar una segunda solicitud de reembolso para el MISMO ticket
                si ya tiene una pendiente.
        """
        # Crear una solicitud pendiente primero (sin mockear para asegurar que existe en DB para la validación)
        RefundRequest.objects.create(
            user=self.buyer,
            ticket_code=self.ticket_code_str,
            reason="Primera solicitud E2E",
            additional_details="Detalles de la primera E2E.",
            accepted_policy=True,
            approval=None, # Pendiente
            event_name=self.event.title
        )

        self.client.force_login(self.buyer)
        url = reverse("refund_form", kwargs={"id": self.ticket.id})

        data = {
            "ticket_code": self.ticket_code_str,
            "reason": "Segunda solicitud E2E",
            "additional_details": "Debería fallar E2E.",
            "accepted_policy": "on"
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200) # Renderiza el formulario con error
        # AQUI ES DONDE CAMBIAMOS EL MENSAJE ESPERADO PARA QUE COINCIDA CON LA VISTA
        self.assertContains(response, "Ya tienes una solicitud de reembolso pendiente.")

        # Asegurarse de que mock_notification_create NO fue llamado para la segunda solicitud
        mock_notification_create.assert_not_called()
        
        # Asegurarse de que no se creó una segunda solicitud en la DB
        self.assertEqual(RefundRequest.objects.filter(user=self.buyer, ticket_code=self.ticket_code_str).count(), 1)


    @patch('app.views.Notification.objects.create')
    def test_user_can_submit_refund_request_for_different_tickets(self, mock_notification_create):
        """
        Test 3: Un usuario PUEDE enviar solicitudes de reembolso para tickets DIFERENTES,
                incluso si tiene una solicitud pendiente para otro ticket.
        """
        # Crear una primera solicitud de reembolso pendiente para self.ticket
        RefundRequest.objects.create(
            user=self.buyer,
            ticket_code=self.ticket_code_str,
            reason="Pendiente para ticket 1 E2E",
            additional_details="Detalles.",
            accepted_policy=True,
            approval=None,
            event_name=self.event.title
        )

        # Crear un SEGUNDO evento y un segundo ticket para el mismo comprador
        event_2 = Event.objects.create(
            title='Concierto 2 E2E',
            description='Segundo concierto E2E',
            scheduled_at=timezone.make_aware(datetime.datetime(2026, 1, 15, 19, 0, 0)),
            organizer=self.organizer,
            venue=self.venue,
            state=Event.ACTIVE,
            category=self.category # Asignar la categoría directamente
        )

        ticket_2 = Ticket.objects.create(
            event=event_2,
            user=self.buyer,
            type=Ticket.GENERAL,
            quantity=1,
        )
        ticket_2_code_str = str(ticket_2.ticket_code)


        self.client.force_login(self.buyer)
        url_ticket_2 = reverse("refund_form", kwargs={"id": ticket_2.id})

        data_ticket_2 = {
            "ticket_code": ticket_2_code_str,
            "reason": "Solicitud para segundo ticket E2E",
            "additional_details": "Quiero reembolsar el ticket del segundo evento E2E.",
            "accepted_policy": "on"
        }

        response_ticket_2 = self.client.post(url_ticket_2, data_ticket_2)

        self.assertEqual(response_ticket_2.status_code, 302)
        self.assertRedirects(response_ticket_2, reverse("tickets"))

        # Verificar que se crearon dos solicitudes de reembolso en total para el usuario
        all_requests_for_buyer = RefundRequest.objects.filter(user=self.buyer)
        self.assertEqual(all_requests_for_buyer.count(), 2)

        refund_request_2 = RefundRequest.objects.get(ticket_code=ticket_2_code_str)
        self.assertIsNotNone(refund_request_2)
        self.assertEqual(refund_request_2.user, self.buyer)
        self.assertIsNone(refund_request_2.approval)

        # Verificamos que mock_notification_create fue llamado dos veces en total
        # (una por el primer test_case exitoso, y otra por este test_case exitoso)
        # Esto requiere que los tests NO se limpien por completo entre sí, pero TestCase sí lo hace.
        # Por lo tanto, en este test_case, debería ser llamado 1 vez.
        mock_notification_create.assert_called_once()