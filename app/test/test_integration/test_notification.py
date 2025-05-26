from django.test import Client, TestCase
from django.urls import reverse
from app.models import Notification, User, Event, Venue, Ticket

class BaseNotificationTestCase(TestCase):
    def setUp(self):
        self.mocked_user = User.objects.create_user(username="regular", password="password123")
        self.mocked_organizer_user = User.objects.create_user(username="admin", password="password123", is_organizer=True)
        self.mocked_venue = Venue.objects.create(
            name="Centro Cultural Recoleta",
            address="Junín 1930",
            capacity=500,
            country="AR",
            city="Buenos Aires"
        )

        self.event_mocked = Event.objects.create(
            title="Mocked Event",
            description="Test description",
            scheduled_at="2025-12-01T10:00:00Z",
            organizer=self.mocked_organizer_user,
            venue=self.mocked_venue
        )

        self.mocked_notification = Notification.new(
            [self.mocked_user, self.mocked_organizer_user], 
            self.event_mocked,
            "This is a title", 
            "This is a message", 
            "LOW"
        )

        self.mocked_ticket = Ticket.objects.create(
            user=self.mocked_user,
            event=self.event_mocked,
            ticket_code=2,
            quantity=2,  
            type='vip'
        )

        self.client = Client()

class NotificationsListViewTest(BaseNotificationTestCase):
    def test_notifications_view_with_regular_user(self):
        self.client.login(username="regular", password="password123")

        response = self.client.get(reverse("notifications"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/notifications.html")
        self.assertIn("notifications", response.context)
       
        notifications = list(response.context["notifications"])
        self.assertEqual(notifications[0], self.mocked_notification)

    def test_notifications_view_with_organizers_user(self):
        self.client.login(username="admin", password="password123")

        response = self.client.get(reverse("notifications"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/notifications_admin.html")
        self.assertIn("notifications", response.context)
       
        notifications = list(response.context["notifications"])
        self.assertEqual(notifications[0], self.mocked_notification)

        self.assertTrue(response.context["user_is_organizer"])

class NotificationsByEventChangeTest(BaseNotificationTestCase):
    def test_create_notification_by_event_change(self):
        self.client.login(username="admin", password="password123")

        event_id = self.event_mocked.pk
        mocked_data = {
            "title": "Evento Actualizado",
            "description": "Nueva descripción",
            "date": "2025-06-15",
            "time": "16:45",
        }

        response = self.client.post(reverse("event_edit", args=[event_id]), mocked_data)

        notifications = Notification.objects.filter(event=self.event_mocked, title="Evento Modificado")
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(len(notifications) >= 1)
       
    def test_not_create_notification_by_event_change(self):
        self.client.login(username="admin", password="password123")

        event_id = 0
        mocked_data = {
            "title": "Evento Actualizado",
            "description": "Nueva descripción",
            "date": "2025-06-15",
            "time": "16:45",
        }

        response = self.client.post(reverse("event_edit", args=[event_id]), mocked_data)

        notifications = Notification.objects.filter(event=self.event_mocked, title="Evento Modificado")
        
        self.assertEqual(response.status_code, 404)
        self.assertFalse(len(notifications) >= 1)