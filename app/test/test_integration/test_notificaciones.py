from django.urls import reverse
import datetime

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import Event, Notification, User


class BaseEventTestCase(TestCase):
    """Clase base con la configuración común para todos los tests de notificaciones"""

    def setUp(self):
        # Crear un usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )

        # Crear un usuario regular
        self.regular_user = User.objects.create_user(
            username="regular",
            email="regular@test.com",
            password="password123",
            is_organizer=False,
        )

        # Crear algunos eventos de prueba
        self.event1 = Event.objects.create(
            title="Evento 1",
            description="Descripción del evento 1",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
        )

        # Cliente para hacer peticiones
        self.client = Client()


class NotificationList(BaseEventTestCase):
    """Tests para la vista de listado de eventos"""

    def test_create_notifications(self):
        """Test que verifica la creación de la notificación"""
        # Login con usuario organizador
        self.client.login(username="organizador", password="password123")

        # Crear una notificacion de prueba
        notification_data = { 
            "title": "Evento de prueba",
            "massage": "Mensaje de la notificación",
            "priority": "Low",
            "is_read": False,
            "recipient": "all",
            "event": self.event1.id,  # type: ignore
        }

        # Hacer petición POST a la vista notification_create
        response = self.client.post(reverse("notification_create"), notification_data)

        # Verificar que redirecciona a events
        self.assertEqual(response.status_code, 302)

        # Verificar que se creó el evento
        self.assertTrue(Notification.objects.filter(title="Evento de prueba").exists())
        notification = Notification.objects.get(title="Evento de prueba")
        self.assertEqual(notification.massage, "Mensaje de la notificación")
        self.assertEqual(notification.Priority, "Low") # type: ignore
        self.assertEqual(notification.is_read, False)
        self.assertEqual(notification.event.id, self.event1.id) # type: ignore
