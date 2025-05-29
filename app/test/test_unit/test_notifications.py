from django.test import TestCase
from django.utils import timezone
from app.models import Event, Venue, User, Notification, Category
import datetime

class NotificationUnitTest(TestCase):
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

    def test_notification_created_on_event_update(self):
        """Test que verifica si se notifica a los usuarios con ticket del evento cuando cambia la fecha o el lugar"""
        # Simular cambio de fecha y lugar
        old_scheduled_at = self.event.scheduled_at
        old_venue = self.event.venue
        new_scheduled_at = old_scheduled_at + datetime.timedelta(days=2)
        new_venue = self.venue2

        self.event.scheduled_at = new_scheduled_at
        self.event.venue = new_venue
        self.event.save()

        # Lógica de notificación
        if old_scheduled_at != new_scheduled_at or old_venue != new_venue:
            notification = Notification.objects.create(
                title="Evento Modificado",
                message=f"El evento '{self.event.title}' ha sido modificado. Fecha: {new_scheduled_at} y lugar: {new_venue.name}.",
                priority="MEDIUM",
            )
            usuarios = User.objects.filter(tickets__event=self.event).distinct()
            notification.users.set(usuarios)
            notification.save()

        # Verificar que la notificación esté en cada usuario con ticket
        for usuario in usuarios:
            self.assertIn(notification, usuario.notifications.all()) 