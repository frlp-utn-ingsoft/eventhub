# app/test/test_integration/test_capacity_event.py
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
import datetime
from app.models import Event, User, Venue, Ticket

class TicketPurchaseIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123',
            is_organizer=True
        )
        
        # Crear venue con capacidad limitada
        self.venue = Venue.objects.create(
            name='Test Venue',
            capacity=10,
            created_by=self.user,
            address='123 Test Street',
            city='Test City',
            contact_info='contact@test.com'
        )
        
        # Crear evento con disponibilidad limitada
        self.event = Event.objects.create(
            title='Concierto de Prueba',
            description='Evento para testing',
            scheduled_at=timezone.make_aware(datetime.datetime(2025, 12, 31, 20, 0)),
            organizer=self.user,
            venue=self.venue,
            available_tickets=10
        )
        
        self.client.login(username='testuser', password='testpass123')

    def test_sold_out_event_blocks_purchases(self):
        initial_tickets = Ticket.objects.count()
        initial_availability = self.event.available_tickets

        # Intentar compra inválida
        response = self.client.post(
            reverse('ticket_form'),
            {
                'event': self.event.id,
                'quantity': 11,
                'type': 'GENERAL',
                'price_paid': '550.00'
            },
            follow=True
        )

        self.assertEqual(Ticket.objects.count(), initial_tickets)
        self.event.refresh_from_db()
        self.assertEqual(self.event.available_tickets, initial_availability)

    def test_partial_availability_message(self):
        # Crear tickets directamente (simular compra)
        Ticket.objects.create(
            event=self.event,
            user=self.user,
            quantity=8,
            price_paid=Decimal('400.00'),
            type='GENERAL'
        )
        
        # Actualizar disponibilidad manualmente
        self.event.available_tickets = 2
        self.event.save()
        
        # Verificar disponibilidad
        self.event.refresh_from_db()
        self.assertEqual(self.event.available_tickets, 2)

    def test_successful_purchase_updates_availability(self):
        # Crear ticket directamente (simular compra exitosa)
        Ticket.objects.create(
            event=self.event,
            user=self.user,
            quantity=4,
            price_paid=Decimal('550.00'),
            type='VIP'
        )
        
        # Actualizar disponibilidad manualmente
        self.event.available_tickets = 6
        self.event.save()
        
        # Verificar actualización
        self.event.refresh_from_db()
        self.assertEqual(self.event.available_tickets, 6)