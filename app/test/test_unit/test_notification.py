from django.test import TestCase
from app.models import Notification, User, Event, NotificationUser, Venue, Ticket, NotificationUser
from app.validations.notifications import createNotificationValidations

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

class TestCreateNotificationValidations(TestCase):
    def setUp(self):
        self.valid_data = {
            "user_ids": [1],
            "event_id": 1,
            "title": "Título válido",
            "message": "Mensaje válido",
            "priority": "LOW"
        }

    def test_valid_data(self):
        valid, errors = createNotificationValidations(**self.valid_data)
        self.assertTrue(valid)
        self.assertEqual(errors, {})

    def test_empty_title(self):
        data = self.valid_data.copy()
        data["title"] = "   "
        valid, errors = createNotificationValidations(**data)
        self.assertFalse(valid)
        self.assertIn("title", errors)

    def test_title_too_long(self):
        data = self.valid_data.copy()
        data["title"] = "a" * 51
        valid, errors = createNotificationValidations(**data)
        self.assertFalse(valid)
        self.assertIn("title", errors)

    def test_empty_message(self):
        data = self.valid_data.copy()
        data["message"] = "   "
        valid, errors = createNotificationValidations(**data)
        self.assertFalse(valid)
        self.assertIn("message", errors)

    def test_message_too_long(self):
        data = self.valid_data.copy()
        data["message"] = "a" * 101
        valid, errors = createNotificationValidations(**data)
        self.assertFalse(valid)
        self.assertIn("message", errors)

    def test_empty_priority(self):
        data = self.valid_data.copy()
        data["priority"] = ""
        valid, errors = createNotificationValidations(**data)
        self.assertFalse(valid)
        self.assertIn("priority", errors)

    def test_invalid_priority(self):
        data = self.valid_data.copy()
        data["priority"] = "URGENT"
        valid, errors = createNotificationValidations(**data)
        self.assertFalse(valid)
        self.assertIn("priority", errors)

    def test_empty_user_ids(self):
        data = self.valid_data.copy()
        data["user_ids"] = []
        valid, errors = createNotificationValidations(**data)
        self.assertFalse(valid)
        self.assertIn("user", errors)

    def test_missing_event_id(self):
        data = self.valid_data.copy()
        data["event_id"] = None
        valid, errors = createNotificationValidations(**data)
        self.assertFalse(valid)
        self.assertIn("event", errors)

    def test_multiple_errors(self):
        data = {
            "user_ids": [],
            "event_id": None,
            "title": " " * 5,
            "message": "",
            "priority": "URGENT"
        }
        valid, errors = createNotificationValidations(**data)
        self.assertFalse(valid)
        self.assertEqual(len(errors), 5)