from django.test import TestCase
from django.utils.timezone import now, timedelta, localtime
from app.models import Event, Notification, Ticket, User, Venue, User_Notification

class EventNotificationIntegrationTest(TestCase):

    def setUp(self):
        self.organizer = User.objects.create_user(username="organizador", password="pass", is_organizer=True)
        self.user1 = User.objects.create_user(username="user1", password="pass")
        self.user2 = User.objects.create_user(username="user2", password="pass")

        self.venue = Venue.objects.create(
            name="Lugar Original",
            address="Dirección 123",
            city="Ciudad",
            capacity=1000,
            contact="contacto@lugar.com"
        )

        self.event = Event.objects.create(
            title="Evento de Prueba",
            description="Descripción del evento",
            scheduled_at=now() + timedelta(days=2),
            organizer=self.organizer,
            venue=self.venue
        )

        # Crear tickets para ambos usuarios
        Ticket.objects.create(event=self.event, user=self.user1, quantity=1, type="GENERAL")
        Ticket.objects.create(event=self.event, user=self.user2, quantity=2, type="GENERAL")

    def test_notifications_created_for_all_ticket_users_on_event_change(self):
        old_date = localtime(self.event.scheduled_at)  
        old_venue = self.event.venue

        new_venue = Venue.objects.create(
            name="Lugar Nuevo",
            address="Calle 456",
            city="Ciudad Nueva",
            capacity=500,
            contact="nuevo@lugar.com"
        )
        self.event.scheduled_at = old_date + timedelta(hours=5)
        self.event.venue = new_venue  # type: ignore
        self.event.save()

        notif = Notification.objects.filter(event=self.event).last()

        user1_notifs = self.user1.notificaciones.filter(event=self.event)  # type: ignore
        user2_notifs = self.user2.notificaciones.filter(event=self.event)  # type: ignore

        self.assertEqual(user1_notifs.count(), 1, "User1 no recibió notificación")
        self.assertEqual(user2_notifs.count(), 1, "User2 no recibió notificación")
        self.assertEqual(Notification.objects.filter(event=self.event).count(), 1)

        self.assertIn("Evento de Prueba", notif.title)  # type: ignore
        self.assertIn(old_date.strftime("%d/%m/%Y"), notif.title)  # type: ignore
        self.assertIn(old_venue.name, notif.title)  # type: ignore
        self.assertIn("la fecha de", notif.message)  # type: ignore
        self.assertIn("el lugar de", notif.message)  # type: ignore
        self.assertEqual(notif.priority, "High")  # type: ignore

        self.assertTrue(
            User_Notification.objects.filter(user=self.user1, notification=notif).exists(),
            "No se creó User_Notification para user1"
        )
        self.assertTrue(
            User_Notification.objects.filter(user=self.user2, notification=notif).exists(),
            "No se creó User_Notification para user2"
        )
