import datetime

from django.test import TestCase
from django.utils import timezone

from app.models import Event, User, Ticket, Notification
from app.views.event_views import filter_events, handle_notification_on_reprogramate



class NotificationTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador_test",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )
        self.other_user = User.objects.create_user(
            username="other_organizador_test",
            email="other_organizador@example.com",
            password="password123",
            is_organizer=True,
        )

    def test_creation_notification_in_event_update(self):
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
        )
        Ticket.new(user=self.other_user, event=event, quantity=3, ticket_type="GENERAL")

        title="Evento de prueba"
        description="Descripción del evento de prueba"
        organizer=self.organizer
        
        var = timezone.now() + datetime.timedelta(days=1)

        # envia la notificacion
        handle_notification_on_reprogramate(
            event, 
            title,
            categories=[], # type: ignore
            venue=None, # type: ignore
            description= description,
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            user=organizer
        )

        # Recupera las notificaciones del usuario
        notifications = Notification.objects.filter(addressee=self.other_user)
        success = False
        for n in notifications:
            if n.event == event and n.title == "El evento ha sido reprogramado":
                if n.event.scheduled_at.strftime("%Y-%m-%d %H:%M") == var.strftime("%Y-%m-%d %H:%M"): # type: ignore
                    success = True
                break
        self.assertEqual(success, True, "El usuario no recibió la notificación de cambio de fecha del evento")