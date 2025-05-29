from django.test import TestCase
from app.models import User, Event, Venue, Ticket
from django.utils import timezone
from datetime import timedelta
from typing import Dict, Any, Union, Tuple

class TestOverselling(TestCase):
    def setUp(self):
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Crear venue de prueba con capacidad limitada
        self.venue = Venue.objects.create(
            name='Test Venue',
            adress='Test Address',
            city='Test City',
            capacity=10,  # Capacidad de 10 personas
            contact='Test Contact'
        )
        
        # Crear evento de prueba
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            scheduled_at=timezone.now() + timedelta(days=1),
            organizer=self.user,
            venue=self.venue
        )

    def test_cannot_buy_more_tickets_than_capacity(self):
        """Verifica que no se puedan comprar más entradas que la capacidad disponible"""
        # Intentar comprar 11 entradas (más que la capacidad de 10)
        success, result = Ticket.new(
            quantity=11,
            type='GENERAL',
            event=self.event,
            user=self.user
        )
        
        self.assertFalse(success)
        self.assertIsInstance(result, dict)
        self.assertIn('quantity', result)
        self.assertEqual(
            result['quantity'],
            'Puedes comprar 4 lugares como máximo.'
        )

    def test_cannot_buy_tickets_when_event_is_full(self):
        """Verifica que no se puedan comprar entradas cuando el evento está lleno"""
        # Primero llenamos el evento con múltiples usuarios
        users = []
        for i in range(3):  # Necesitamos 3 usuarios para comprar 10 entradas (4+4+2)
            user = User.objects.create_user(
                username=f'testuser{i}',
                password='testpass123'
            )
            users.append(user)
        
        # Primer usuario compra 4 entradas
        success, ticket1 = Ticket.new(
            quantity=4,
            type='GENERAL',
            event=self.event,
            user=users[0]
        )
        self.assertTrue(success)
        
        # Segundo usuario compra 4 entradas
        success, ticket2 = Ticket.new(
            quantity=4,
            type='GENERAL',
            event=self.event,
            user=users[1]
        )
        self.assertTrue(success)
        
        # Tercer usuario compra 2 entradas
        success, ticket3 = Ticket.new(
            quantity=2,
            type='GENERAL',
            event=self.event,
            user=users[2]
        )
        self.assertTrue(success)
        
        # Intentar comprar una entrada más
        success, result = Ticket.new(
            quantity=1,
            type='GENERAL',
            event=self.event,
            user=self.user
        )
        
        self.assertFalse(success)
        self.assertIsInstance(result, dict)
        self.assertIn('event', result)
        self.assertEqual(
            result['event'],
            'Lo sentimos, este evento ya no tiene entradas disponibles'
        )

    def test_cannot_update_ticket_to_exceed_capacity(self):
        """Verifica que no se pueda actualizar un ticket para exceder la capacidad"""
        # Crear un ticket inicial con 4 entradas
        success, ticket = Ticket.new(
            quantity=4,
            type='GENERAL',
            event=self.event,
            user=self.user
        )
        self.assertTrue(success)
        self.assertIsInstance(ticket, Ticket)
        
        # Intentar actualizar el ticket a 7 entradas (lo que excedería la capacidad)
        # Primero validamos la cantidad
        errors = Ticket.validate(
            quantity=7,
            type='GENERAL',
            event=self.event,
            user=self.user
        )
        
        self.assertIn('quantity', errors)
        self.assertEqual(
            errors['quantity'],
            'Puedes comprar 4 lugares como máximo.'
        )

    def test_can_buy_tickets_up_to_capacity(self):
        """Verifica que se puedan comprar entradas hasta la capacidad máxima"""
        # Crear múltiples usuarios para comprar hasta la capacidad
        users = []
        for i in range(3):  # Necesitamos 3 usuarios para comprar 10 entradas (4+4+2)
            user = User.objects.create_user(
                username=f'testuser{i}',
                password='testpass123'
            )
            users.append(user)
        
        # Primer usuario compra 4 entradas
        success, ticket1 = Ticket.new(
            quantity=4,
            type='GENERAL',
            event=self.event,
            user=users[0]
        )
        self.assertTrue(success)
        
        # Segundo usuario compra 4 entradas
        success, ticket2 = Ticket.new(
            quantity=4,
            type='GENERAL',
            event=self.event,
            user=users[1]
        )
        self.assertTrue(success)
        
        # Tercer usuario compra 2 entradas
        success, ticket3 = Ticket.new(
            quantity=2,
            type='GENERAL',
            event=self.event,
            user=users[2]
        )
        self.assertTrue(success)
        
        self.assertEqual(self.event.available_tickets(), 0)

    def test_multiple_tickets_respect_capacity(self):
        """Verifica que múltiples compras de tickets respeten la capacidad total"""
        # Crear múltiples usuarios
        users = []
        for i in range(3):
            user = User.objects.create_user(
                username=f'testuser{i}',
                password='testpass123'
            )
            users.append(user)
        
        # Primera compra: 4 entradas
        success, ticket1 = Ticket.new(
            quantity=4,
            type='GENERAL',
            event=self.event,
            user=users[0]
        )
        self.assertTrue(success)
        self.assertIsInstance(ticket1, Ticket)
        
        # Segunda compra: 4 entradas
        success, ticket2 = Ticket.new(
            quantity=4,
            type='GENERAL',
            event=self.event,
            user=users[1]
        )
        self.assertTrue(success)
        self.assertIsInstance(ticket2, Ticket)
        
        # Tercera compra: 3 entradas (debería fallar porque solo quedan 2 disponibles)
        success, result = Ticket.new(
            quantity=3,
            type='GENERAL',
            event=self.event,
            user=users[2]
        )
        
        self.assertFalse(success)
        self.assertIsInstance(result, dict)
        self.assertIn('quantity', result)
        self.assertEqual(
            result['quantity'],
            'No hay suficientes entradas disponibles. Solo quedan 2 entradas.'
        )
