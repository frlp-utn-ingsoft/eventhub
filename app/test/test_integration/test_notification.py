from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from app.models import Notification, User, Event, Venue, Ticket

class BaseNotificationTestCase(TestCase):
    def setUp(self):
        self.mocked_user = User.objects.create_user(username="regular", password="password123")
        self.mocked_organizer_user = User.objects.create_user(username="admin", password="password123", is_organizer=True)
        self.mocked_venue1 = Venue.objects.create(
            name="name",
            address="Junín 1930",
            capacity=500,
            country="AR",
            city="Buenos Aires"
        )

        self.mocked_venue2 = Venue.objects.create(
            name="Auditorio Belgrano",
            address="Virrey Loreto 2348",
            capacity=750,
            country="AR",
            city="CABA"
        )

        self.event_mocked = Event.objects.create(
            title="Mocked Event",
            description="Test description",
            scheduled_at=timezone.make_aware(timezone.datetime(int(2025), int(5), int(15), int(10), int(0))),
            organizer=self.mocked_organizer_user,
            venue=self.mocked_venue1
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
    def test_create_notification_by_date_change(self):
        expected_notifications_number = len(Notification.objects.all()) + 1
        expected_status_code = 302

        event_id = self.event_mocked.pk
        mocked_data = {
            "title": self.event_mocked.title,
            "description": self.event_mocked.description,
            "date": "2025-06-15",
            "time": "16:45",
            "venue": self.event_mocked.venue.pk
        }

        self.client.login(username="admin", password="password123")
        response = self.client.post(reverse("event_edit", args=[event_id]), mocked_data)

        notifications = Notification.objects.filter(event=self.event_mocked)
        
        self.assertEqual(expected_status_code, response.status_code)
        self.assertEqual(expected_notifications_number, len(notifications))
       
    def test_create_notification_by_venue_change(self):
        expected_notifications_number = len(Notification.objects.all()) + 1
        expected_status_code = 302

        event_id = self.event_mocked.pk
        mocked_data = {
            "title": self.event_mocked.title,
            "description": self.event_mocked.description,
            "date": self.event_mocked.scheduled_at.strftime("%Y-%m-%d"),
            "time": self.event_mocked.scheduled_at.strftime("%H:%M"),
            "venue": self.mocked_venue2.pk
        }

        self.client.login(username="admin", password="password123")
        response = self.client.post(reverse("event_edit", args=[event_id]), mocked_data)

        notifications = Notification.objects.filter(event=self.event_mocked)
        
        self.assertEqual(expected_status_code, response.status_code)
        self.assertEqual(expected_notifications_number, len(notifications))

class NotificationNotCreatedByEventChangeTest(BaseNotificationTestCase):
    def test_event_title_and_change(self):
        expected_notifications_number = len(Notification.objects.all())
        expected_status_code = 302

        event_id = self.event_mocked.pk
        mocked_data = {
            "title": self.event_mocked.title + " - Modificado",
            "description": self.event_mocked.description + " - Modificado",
            "date": self.event_mocked.scheduled_at.strftime("%Y-%m-%d"),
            "time": self.event_mocked.scheduled_at.strftime("%H:%M"),
            "venue": self.event_mocked.venue.pk
        }

        self.client.login(username="admin", password="password123")
        response = self.client.post(reverse("event_edit", args=[event_id]), mocked_data)

        notifications = Notification.objects.filter(event=self.event_mocked)
        
        self.assertEqual(expected_status_code, response.status_code)
        self.assertEqual(expected_notifications_number, len(notifications))
