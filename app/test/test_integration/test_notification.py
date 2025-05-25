from django.test import Client, TestCase
from django.urls import reverse
from app.models import Notification, User, Event, NotificationUser, Venue

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
            [self.mocked_organizer_user], 
            self.event_mocked,
            "This is a title", 
            "This is a message", 
            "LOW"
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

   