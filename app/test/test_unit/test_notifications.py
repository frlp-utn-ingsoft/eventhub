from django.test import TestCase
from django.utils import timezone
from app.models import Event, Venue, User, Notification, Category, Ticket
import datetime

class NotificationUnitTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username="organizer", password="pass")
        self.oldVenue = Venue.objects.create(name="Lugar 1", capacity=100)
        self.newVenue = Venue.objects.create(name="Lugar 2", capacity=100)
        self.oldScheduledAt = timezone.now() + datetime.timedelta(days=1)
        self.newScheduledAt = timezone.now() + datetime.timedelta(days=2)
        self.category = Category.objects.create(name="Cat", is_active=True)
        self.user = User.objects.create_user(username='att', password='pass')
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=self.oldScheduledAt,
            organizer=self.organizer,
            venue=self.oldVenue,
            category=self.category,
        )
        self.ticket = Ticket.objects.create(
            event=self.event,
            user=self.user,
            type="GENERAL",
            quantity=1
        )

    def test_notification_created_on_event_update(self):
        """Test que verifica si se notifica a los usuarios con ticket del evento cuando cambia la fecha o el lugar"""
        ##Simulamos el update (cambio de fecha y lugar)
        self.event.scheduled_at = self.newScheduledAt
        self.event.venue = self.newVenue
        self.event.save()
        ##Llamamos al método que crea las notificaciones
        self.event.create_notification_on_event_update(self.oldVenue,self.oldScheduledAt)
        ##Verificamos si: 1) se creo la notifiacion 2)El usuario con ticket fue notificado
        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.first()
        self.assertIn(self.user, notification.users.all())

        