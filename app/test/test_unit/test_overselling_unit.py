from django.test import TestCase
from app.models import User, Event, Venue, Ticket
from django.utils import timezone
from datetime import timedelta
from typing import Dict, List

class TestOverselling(TestCase):
    def setUp(self):
        # Crear organizador y usuario normal
        self.organizer = self._create_test_user('organizer', 'organizerpass123')
        self.user = self._create_test_user('normaluser', 'userpass123')
        
        # Crear venue de prueba con capacidad limitada a 1
        self.venue = Venue.objects.create(
            name='Test Venue',
            adress='Test Address',
            city='Test City',
            capacity=1,
            contact='Test Contact'
        )
        
        # Crear dos eventos
        self.event1 = Event.objects.create(
            title='Test Event 1',
            description='Test Description 1',
            scheduled_at=timezone.now() + timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue
        )
        
        self.event2 = Event.objects.create(
            title='Test Event 2',
            description='Test Description 2',
            scheduled_at=timezone.now() + timedelta(days=2),
            organizer=self.organizer,
            venue=self.venue
        )

    def _create_test_user(self, username: str, password: str) -> User:
        """Helper method para crear usuarios de prueba - optimizado para evitar repetición"""
        return User.objects.create_user(username=username, password=password)

    def _create_multiple_users(self, count: int, base_username: str = 'testuser') -> List[User]:
        """Helper method para crear múltiples usuarios usando bulk_create - optimizado para performance"""
        users_to_create = [
            User(username=f'{base_username}{i}', password='testpass123')
            for i in range(count)
        ]
        return User.objects.bulk_create(users_to_create)

    def _verify_ticket_error(self, success: bool, result: Dict[str, str], expected_key: str, expected_message: str):
        """Helper method para verificar errores de tickets - optimizado para evitar repetición"""
        self.assertFalse(success)
        self.assertIsInstance(result, dict)
        self.assertIn(expected_key, result)
        self.assertEqual(result[expected_key], expected_message)

    def _verify_ticket_success(self, success: bool, ticket: Ticket) -> Ticket:
        """Helper method para verificar éxito de tickets - optimizado para evitar repetición"""
        self.assertTrue(success)
        self.assertIsInstance(ticket, Ticket)
        return ticket

    def test_cannot_buy_more_tickets_than_capacity(self):
        """Verifica que no se puedan comprar más entradas que la capacidad disponible"""
        success, result = Ticket.new(
            quantity=2,
            type='GENERAL',
            event=self.event1,
            user=self.user
        )
        
        # Verificar que es un error de cantidad
        self.assertFalse(success)
        self.assertIsInstance(result, dict)
        if isinstance(result, dict):
            self.assertIn('quantity', result)
            self.assertEqual(
                result['quantity'],
                'No hay suficientes entradas disponibles. Solo quedan 1 entradas.'
            )

    def test_cannot_buy_tickets_when_event_is_full(self):
        """Verifica que no se puedan comprar entradas cuando el evento está lleno"""
        # Comprar la única entrada disponible
        success1, ticket1 = Ticket.new(
            quantity=1,
            type='GENERAL',
            event=self.event1,
            user=self.user
        )
        self.assertTrue(success1)
        self.assertIsInstance(ticket1, Ticket)
        
        # Intentar comprar una entrada más cuando el evento está lleno
        success2, result = Ticket.new(
            quantity=1,
            type='GENERAL',
            event=self.event1,
            user=self.user
        )
        
        # Verificar que es un error de evento lleno
        self.assertFalse(success2)
        self.assertIsInstance(result, dict)
        if isinstance(result, dict):
            self.assertIn('event', result)
            self.assertEqual(
                result['event'],
                'Lo sentimos, este evento ya no tiene entradas disponibles'
            )

    def test_multiple_tickets_respect_capacity(self):
        """Verifica que múltiples compras de tickets respeten la capacidad total"""
        # Comprar la única entrada disponible del evento2
        success1, ticket1 = Ticket.new(quantity=1, type='GENERAL', event=self.event2, user=self.user)
        self.assertTrue(success1)
        self.assertIsInstance(ticket1, Ticket)
        
        # Intentar comprar más entradas cuando no hay disponibles
        success2, result = Ticket.new(
            quantity=1,
            type='GENERAL',
            event=self.event2,
            user=self.user
        )
        
        # Verificar que es un error de cantidad insuficiente
        self.assertFalse(success2)
        self.assertIsInstance(result, dict)
        if isinstance(result, dict):
            self.assertIn('event', result)
            self.assertEqual(
                result['event'],
                'Lo sentimos, este evento ya no tiene entradas disponibles'
            )
