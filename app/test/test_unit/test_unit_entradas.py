from django.test import TestCase
from app.models import Event, Ticket, User, Venue
from datetime import datetime, timedelta

class EventModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.venue = Venue.objects.create(
            name='Test Venue', address='123 St', city='City', capacity=100, contact_info='contact', created_by=self.user
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            scheduled_at=datetime.now() + timedelta(days=10),
            organizer=self.user,
            venue=self.venue
        )

    def test_entradas_vendidas_y_estado_demanda(self):
        self.assertEqual(self.event.entradas_vendidas(), 0)
        self.assertEqual(self.event.estado_demanda(), 'Baja demanda')

        Ticket.objects.create(user=self.user, event=self.event, quantity=95, price_paid=100)
        self.assertEqual(self.event.entradas_vendidas(), 95)
        self.assertEqual(self.event.estado_demanda(), 'Alta demanda')