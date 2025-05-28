from django.test import TestCase
from django.utils.timezone import now, timedelta, localtime
from app.models import Event, Notification, Ticket, User, Venue

class EventNotificationUnitTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username="org", password="pass", is_organizer=True)
        self.user = User.objects.create_user(username="user", password="pass")
        self.venue1 = Venue.objects.create(
            name="Lugar 1",
            address="Calle 123",
            city="Ciudad",
            capacity=100,
            contact="contacto@lugar1.com"
        )
        self.venue2 = Venue.objects.create(
            name="Lugar 2",
            address="Avenida Siempre Viva 456",
            city="Ciudad",
            capacity=200,
            contact="contacto@lugar2.com"
        )

        self.event = Event.objects.create(
            title="Evento Test",
            scheduled_at=now() + timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue1
        )
        Ticket.objects.create(event=self.event, user=self.user, quantity=2, type="GENERAL")

    def test_notification_created_on_event_update_date(self):
        old_date = self.event.scheduled_at
        new_date = old_date + timedelta(hours=2)
        self.event.scheduled_at = new_date
        self.event.save()

        notif = Notification.objects.filter(event=self.event).last()
        self.assertIsNotNone(notif, "No se creó la notificación tras la actualización del evento.")
        self.assertIn("Evento Test", notif.title)  # type: ignore
        self.assertIn(localtime(old_date).strftime("%d/%m/%Y"), notif.title)  # type: ignore
        self.assertIn("la fecha de", notif.message)  # type: ignore
        self.assertIn(localtime(old_date).strftime("%d/%m/%Y a las %H:%M Hs."), notif.message)  # type: ignore
        self.assertIn(localtime(new_date).strftime("%d/%m/%Y a las %H:%M Hs."), notif.message)  # type: ignore
        self.assertEqual(notif.priority, "High")  # type: ignore

    def test_notification_created_on_event_update_venue(self):
        old_venue = self.event.venue
        new_venue = Venue.objects.create(
            name="Nuevo Lugar",
            address="Calle Nueva 789",
            city="Ciudad",
            capacity=150,
            contact="contacto@nuevolugar.com"
        )

        self.event.venue = new_venue  # type: ignore
        self.event.save()

        notif = Notification.objects.filter(event=self.event).last()
        self.assertIsNotNone(notif, "No se creó la notificación tras el cambio de lugar del evento.")
        self.assertIn("Evento Test", notif.title)  # type: ignore
        self.assertIn(old_venue.name if old_venue else "N/A", notif.title)  # type: ignore
        self.assertIn("el lugar de", notif.message)  # type: ignore
        self.assertIn(old_venue.name if old_venue else "N/A", notif.message)  # type: ignore
        self.assertIn(new_venue.name if new_venue else "N/A", notif.message)  # type: ignore
        self.assertEqual(notif.priority, "High")  # type: ignore

    def test_notification_created_on_event_update_date_and_venue(self):
        old_date = self.event.scheduled_at
        new_date = old_date + timedelta(hours=3)
        old_venue = self.event.venue
        new_venue = Venue.objects.create(
            name="Lugar Modificado",
            address="Avenida Modificada 321",
            city="Ciudad",
            capacity=180,
            contact="contacto@lugarmodificado.com"
        )

        self.event.venue = old_venue
        self.event.save()

        self.event.scheduled_at = new_date
        self.event.venue = new_venue  # type: ignore
        self.event.save()


        notif = Notification.objects.filter(event=self.event).last()
        self.assertIsNotNone(notif, "No se creó la notificación tras la actualización de fecha y lugar.")
        self.assertIn("Evento Test", notif.title)  # type: ignore
        self.assertIn(localtime(old_date).strftime("%d/%m/%Y"), notif.title)  # type: ignore
        self.assertIn(old_venue.name if old_venue else "N/A", notif.title)  # type: ignore
        self.assertIn("la fecha de", notif.message)  # type: ignore
        self.assertIn(localtime(old_date).strftime("%d/%m/%Y a las %H:%M Hs."), notif.message)  # type: ignore
        self.assertIn(localtime(new_date).strftime("%d/%m/%Y a las %H:%M Hs."), notif.message) # type: ignore
        self.assertIn("el lugar de", notif.message)  # type: ignore
        self.assertIn(old_venue.name if old_venue else "N/A", notif.message)  # type: ignore
        self.assertIn(new_venue.name if new_venue else "N/A", notif.message)  # type: ignore
        self.assertEqual(notif.priority, "High")  # type: ignore
