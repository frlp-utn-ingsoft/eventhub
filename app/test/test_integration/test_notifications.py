from django.test import TestCase
from django.utils import timezone
from app.models import Event, Venue, User, Notification, Category, Ticket
import datetime

class NotificationIntegrationTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username="organizer", password="pass")
        self.venue1 = Venue.objects.create(name="Lugar 1", capacity=100)
        self.venue2 = Venue.objects.create(name="Lugar 2", capacity=100)
        self.category = Category.objects.create(name="Cat", is_active=True)
        self.user1 = User.objects.create_user(username='att', password='pass')
        self.user2 = User.objects.create_user(username='att2', password='pass2')
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue1,
            category=self.category,
        )
        
        # Crear tickets para los usuarios
        Ticket.objects.create(event=self.event, user=self.user1, quantity=1, type="GENERAL")
        Ticket.objects.create(event=self.event, user=self.user2, quantity=1, type="VIP")

    def test_notification_created_on_event_update(self):
        """Test de integración que verifica la creación de notificaciones y su asociación con usuarios"""
        # Verificar estado inicial
        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(self.user1.notifications.count(), 0)
        self.assertEqual(self.user2.notifications.count(), 0)

        # Simular cambio de fecha y lugar
        old_scheduled_at = self.event.scheduled_at
        old_venue = self.event.venue
        new_scheduled_at = old_scheduled_at + datetime.timedelta(days=2)
        new_venue = self.venue2

        # Actualizar el evento usando el método update
        success, updated_event = self.event.update(
            scheduled_at=new_scheduled_at,
            venue=new_venue
        )
        self.assertTrue(success)

        # Verificar que el evento se actualizó correctamente
        self.assertEqual(updated_event.scheduled_at, new_scheduled_at)
        self.assertEqual(updated_event.venue, new_venue)
        self.assertEqual(updated_event.state, Event.REPROGRAMED)

        # Crear notificación
        notification = Notification.objects.create(
            title="Evento Modificado",
            message=f"El evento '{self.event.title}' ha sido modificado. Fecha: {new_scheduled_at} y lugar: {new_venue.name}.",
            priority="MEDIUM",
        )

        # Obtener usuarios con tickets y asociarlos a la notificación
        usuarios = User.objects.filter(tickets__event=self.event).distinct()
        notification.users.set(usuarios)
        notification.save()

        # Verificar que la notificación se creó correctamente
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(notification.title, "Evento Modificado")
        self.assertEqual(notification.priority, "MEDIUM")
        self.assertIn("Fecha:", notification.message)
        self.assertIn("lugar:", notification.message)

        # Verificar que los usuarios tienen la notificación
        for usuario in usuarios:
            self.assertIn(notification, usuario.notifications.all())
            self.assertEqual(usuario.notifications.count(), 1)
            self.assertFalse(usuario.notifications.first().is_read)

        # Verificar que la notificación tiene los usuarios correctos
        self.assertEqual(notification.users.count(), 2)
        self.assertIn(self.user1, notification.users.all())
        self.assertIn(self.user2, notification.users.all()) 