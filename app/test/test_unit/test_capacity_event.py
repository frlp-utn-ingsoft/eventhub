from decimal import Decimal
from django.test import TestCase
from django.db import IntegrityError, transaction
from django.utils import timezone
from app.models import Event, User, Venue, Ticket
import datetime

class EventCapacityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.venue = Venue.objects.create(
            name='Test Venue',
            address='123 Street',
            city='City',
            capacity=100,
            contact_info='contact@test.com',
            created_by=self.user
        )
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            scheduled_at=timezone.make_aware(datetime.datetime(2025, 1, 1, 12, 0)),
            organizer=self.user,
            venue=self.venue,
            available_tickets=100
        )

    def test_ticket_purchase_updates_availability(self):
        # Test de compra válida
        ticket = Ticket.objects.create(
            user=self.user,
            event=self.event,
            quantity=5,
            price_paid=Decimal('250.00')
        )
        self.event.refresh_from_db()
        self.assertEqual(self.event.available_tickets, 95)
        self.assertTrue(ticket.ticket_code.startswith('GEN-'))

    def test_cannot_exceed_capacity(self):
        # Test de capacidad excedida
        try:
            with transaction.atomic():
                Ticket.objects.create(
                    user=self.user,
                    event=self.event,
                    quantity=101,
                    price_paid=Decimal('5050.00')
                )
        except IntegrityError:
            pass
            
        self.event.refresh_from_db()
        self.assertEqual(self.event.available_tickets, 100)

    def test_venue_change_updates_availability(self):
        # Test de cambio de venue
        new_venue = Venue.objects.create(
            name='New Venue',
            capacity=200,
            created_by=self.user,
            address='456 Ave',
            city='City',
            contact_info='new@test.com'
        )
        
        self.event.venue = new_venue
        self.event.save()
        self.event.update_availability()
        
        self.event.refresh_from_db()
        self.assertEqual(self.event.available_tickets, 200)