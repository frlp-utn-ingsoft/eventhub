from django.test import TestCase
from app.models import Notification, User, Event, NotificationUser, Venue

class NotificationModelTest(TestCase):
    def setUp(self):
        self.mocked_user = User.objects.create_user(username="testuser", password="12345")
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
            organizer=self.mocked_user,
            venue=self.mocked_venue
        )
        
    def test_create_notification(self):
        expected_title = "This is a title"
        expected_message = "This is a message"
        expected_priority = "LOW"

        notification = Notification.new(
            [self.mocked_user], 
            self.event_mocked,
            expected_title, 
            expected_message, 
            expected_priority
        )

        self.assertEqual(notification.title, expected_title)
        self.assertEqual(notification.message, expected_message)
        self.assertEqual(notification.priority, expected_priority)
        self.assertEqual(notification.event, self.event_mocked)
        self.assertIn(self.mocked_user, notification.users.all())
        self.assertEqual(notification.users.count(), 1)

    def test_mark_as_read_notification(self):
        mocked_user = User.objects.create_user(username="test_mark_as_read_notification", password="12345")
        notification = Notification.new(
            [mocked_user], 
            self.event_mocked,
            "This is a title", 
            "This is a message", 
            "LOW"
        )

        notification.mark_as_read(mocked_user.pk)

        notification_user = NotificationUser.objects.filter(notification=notification, user_id=mocked_user.pk).first()

        self.assertTrue(notification_user.is_read)

    def test_notification_is_mark_as_not_read(self):
        mocked_user = User.objects.create_user(username="test_mark_as_read_notification", password="12345")
        notification = Notification.new(
            [mocked_user], 
            self.event_mocked,
            "This is a title", 
            "This is a message", 
            "LOW"
        )

        notification_user = NotificationUser.objects.filter(notification=notification, user_id=mocked_user.pk).first()

        self.assertFalse(notification_user.is_read)