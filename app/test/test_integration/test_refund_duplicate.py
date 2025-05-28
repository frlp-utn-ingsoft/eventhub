from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from app.models import Event, User, Ticket, RefundRequest, Venue, Category
from django.utils import timezone
from datetime import timedelta
import uuid
from unittest.mock import patch # Importar patch para mockear Notification

User = get_user_model()

class RefundFormDuplicateHandlingIntegrationTests(TestCase):
    def setUp(self):
        # Crear datos de prueba necesarios para la integración con la base de datos
        self.organizer = User.objects.create_user(
            username='organizer_int_dup', email='organizer_int_dup@example.com', password='password', is_organizer=True
        )
        self.buyer = User.objects.create_user(
            username='buyer_int_dup', email='buyer_int_dup@example.com', password='password', is_organizer=False
        )
        self.venue = Venue.objects.create(
            name='Test Venue Int Dup', adress='101 Int Dup St', city='Int Dup City', capacity=50, contact='int_dup@venue.com'
        )
        self.category = Category.objects.create(name='Int Dup Category', description='Int Dup Desc')
        self.event = Event.objects.create(
            title='Evento Duplicado Int',
            description='Evento para testear manejo de duplicados en integración',
            scheduled_at=timezone.now() + timedelta(days=10), # Evento en el futuro
            organizer=self.organizer,
            venue=self.venue,
            state=Event.ACTIVE,
            category=self.category
        )
        self.ticket = Ticket.objects.create(
            event=self.event,
            user=self.buyer,
            type=Ticket.GENERAL,
            quantity=1,
        )
        self.ticket_code_str = str(self.ticket.ticket_code)
        
        self.client = Client() # Cliente de prueba para simular peticiones HTTP

    @patch('app.views.Notification.objects.create') # Mockeamos la creación de Notificaciones para este test
    def test_user_cannot_submit_duplicate_refund_request_for_same_ticket_integration(self, mock_notification_create):
        """
        Integración: Verifica que un usuario no puede enviar una segunda solicitud de reembolso
        para el MISMO ticket si ya tiene una pendiente, probando la interacción real con la DB.
        """
        # Paso 1: Crear una solicitud pendiente REAL en la base de datos
        RefundRequest.objects.create(
            user=self.buyer,
            ticket_code=self.ticket_code_str,
            reason="Primera solicitud Int",
            additional_details="Detalles de la primera Int.",
            accepted_policy=True,
            approval=None, # IMPORTANTE: la dejamos como PENDIENTE
            event_name=self.event.title
        )

        # Autenticar al usuario para la petición
        self.client.force_login(self.buyer)
        url = reverse("refund_form", kwargs={"id": self.ticket.id})

        # Datos para la segunda solicitud (duplicada)
        data = {
            "ticket_code": self.ticket_code_str,
            "reason": "Segunda solicitud Int",
            "additional_details": "Debería fallar Int.",
            "accepted_policy": "on"
        }

        # Paso 2: Enviar la segunda solicitud (duplicada)
        response = self.client.post(url, data)

        # Afirmaciones:
        # La vista debería renderizar el formulario de nuevo con un error (status 200)
        self.assertEqual(response.status_code, 200) 
        # El contenido de la respuesta debe contener el mensaje de error esperado
        self.assertContains(response, "Ya tienes una solicitud de reembolso pendiente.")
        
        # Asegurarse de que la notificación NO fue creada, ya que la solicitud fue bloqueada
        mock_notification_create.assert_not_called()
        
        # Asegurarse de que NO se creó una segunda solicitud en la base de datos
        # Solo debe haber una solicitud (la que creamos manualmente al principio)
        self.assertEqual(RefundRequest.objects.filter(user=self.buyer, ticket_code=self.ticket_code_str).count(), 1)