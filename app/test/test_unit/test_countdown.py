from django.test import TestCase
from django.utils import timezone
from app.models import Event, User, Venue, Ticket
from app.utils import *
from datetime import datetime, timedelta
from django.utils import timezone

class CountDownTest(TestCase):
    def test_count_down_with_future_event(self):
        "Verify that the countdown_timer function returns the correct countdown for a future event."
        future_time = timezone.now() + timezone.timedelta(days=2, hours=3, minutes=15, seconds=30)
        result = countdown_timer(future_time)
        self.assertFalse(result['completed'])
        self.assertEqual(result['days'], 2)
        self.assertEqual(result['hours'], 3)
        self.assertEqual(result['minutes'], 15)

    def test_count_down_with_future_event_same_day(self):
        "Verify that the function correctly handles events scheduled in less than a day."
        scheduled_at= timezone.make_aware((datetime.now() + timedelta(days=0.2)))
        countdown = countdown_timer(scheduled_at)
        self.assertIsNotNone(countdown)
        self.assertIs(countdown["days"], 0)
        self.assertFalse(countdown["completed"])
        
    def test_count_down_with_past_event(self):
        "Verify that the function correctly indicates when the event has already passed."
        scheduled_at= timezone.make_aware((datetime.now() - timedelta(days=2)))
        countdown = countdown_timer(scheduled_at)
        self.assertIsNotNone(countdown)
        self.assertIs(countdown["days"], 0)
        self.assertIs(countdown["hours"], 0)
        self.assertIs(countdown["minutes"], 0)
        self.assertIs(countdown["seconds"], 0)
        self.assertTrue(countdown["completed"])
    
    def test_count_down_with_empty_event(self):
        "Verify that the function returns None if no date is provided."
        countdown = countdown_timer(None)
        self.assertIsNone(countdown)
     
    def test_count_down_with_naive_datetime(self):
        "Verify that the function correctly handles naive (timezone-unaware) dates."
        naive_time = datetime.now() + timedelta(days=1)
        countdown = countdown_timer(naive_time)
        self.assertIsNotNone(countdown)
        self.assertEqual(countdown["days"], 0)
        self.assertFalse(countdown["completed"])

