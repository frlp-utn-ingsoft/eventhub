from django.test import TestCase
from app.models import Notification, User, Event, NotificationUser, Venue, Ticket, NotificationUser

class NotificationModelTest(TestCase):
    def setUp(self):
        self.mocked_user = User.objects.create_user(username="testuser", password="12345")
        self.mocked_organizer = User.objects.create_user(username="testorganizer", password="12345")
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
        self.mocked_ticket = Ticket.objects.create(
            user=self.mocked_user,
            event=self.event_mocked,
            ticket_code=2,
            quantity=2,  
            type='vip'
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

    def test_notification_created_by_event_change(self):
        expectedTitle = "Evento Modificado"
        expectedMessage = "El evento ha sido modificado. Revisa el detalle del evento para mantenerte actualizado."
        expectedPriority = "LOW"

        notification = Notification.notify_event_change(self.event_mocked, self.mocked_organizer)
        notification_user = NotificationUser.objects.filter(notification=notification, user_id=self.mocked_user.pk).first()

        self.assertEqual(expectedTitle, notification.title)
        self.assertEqual(expectedMessage, notification.message)
        self.assertEqual(expectedPriority, notification.priority)
        self.assertEqual(self.event_mocked, notification.event)
        self.assertEqual(self.mocked_user, notification_user.user)