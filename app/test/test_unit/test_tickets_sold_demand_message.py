import datetime

from django.test import TestCase
from django.utils import timezone

from app.models import Event, User, Venue, Ticket


class EventModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organizer = User.objects.create_user(
            username="organizador_test",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )

        cls.not_organizer = User.objects.create_user(
            username="not_organizer_test",
            email="not_organizer@example.com",
            password="password123",
            is_organizer=False,
        )

        cls.venue_mocked = Venue.objects.create(
            name="Auditorio Nacional",
            address="60 y 124",
            capacity=5000,
            country="ARG",  
            city="La Plata"
        )

        cls.event_mocked = Event.objects.create(
            title="Pelicula",
            description="Descripción de la pelicula",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=cls.organizer,
            venue = cls.venue_mocked
        )


    def test_tickets_sold_correct_total(self):
        Ticket.objects.create(user = self.not_organizer, event=self.event_mocked, quantity=100, type="general")

        self.assertEqual(self.event_mocked.tickets_sold, 100)

    def test_tickets_sold_incorrect_total(self):
        Ticket.objects.create(user = self.not_organizer, event=self.event_mocked, quantity=100, type="general")

        self.assertNotEqual(self.event_mocked.tickets_sold, 400)    

    def test_demand_message_low(self):
        Ticket.objects.create(user = self.not_organizer, event=self.event_mocked, quantity=100, type="general")
        self.assertEqual(self.event_mocked.demand_message,  "BAJA")
    
    def test_demand_message_high(self):

        Ticket.objects.create(user = self.not_organizer, event=self.event_mocked, quantity=4600, type="general")
        self.assertEqual(self.event_mocked.demand_message,  "ALTA")

    def test_demand_message_medium(self):
        Ticket.objects.create(user = self.not_organizer, event=self.event_mocked, quantity=700, type="general")
        self.assertEqual(self.event_mocked.demand_message,  "MEDIA")
        
    

        

