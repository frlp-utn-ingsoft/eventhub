from django.test import TestCase
from app.models import User, Event, Venue, Ticket
from django.utils import timezone
from datetime import timedelta
from typing import Dict, Any, Union, Tuple, List

class TestOverselling(TestCase):
    def setUp(self):
        self.user = self._create_test_user('testuser', 'testpass123')
        
        # Crear venue de prueba con capacidad limitada
        self.venue = Venue.objects.create(
            name='Test Venue',
            adress='Test Address',
            city='Test City',
            capacity=10,
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
            quantity=11,
            type='GENERAL',
            event=self.event,
            user=self.user
        )
        
        # Verificar que es un error de cantidad
        self.assertFalse(success)
        self.assertIsInstance(result, dict)
        if isinstance(result, dict):
            self.assertIn('quantity', result)
            self.assertEqual(
                result['quantity'],
                'Puedes comprar 4 lugares como máximo.'
            )

    def test_cannot_buy_tickets_when_event_is_full(self):
        """Verifica que no se puedan comprar entradas cuando el evento está lleno"""
        # Crear múltiples usuarios usando método helper
        users = self._create_multiple_users(count=3)
        
        # Comprar entradas hasta llenar el evento
        success1, ticket1 = Ticket.new(quantity=4, type='GENERAL', event=self.event, user=users[0])
        self.assertTrue(success1)
        self.assertIsInstance(ticket1, Ticket)
        
        success2, ticket2 = Ticket.new(quantity=4, type='GENERAL', event=self.event, user=users[1])
        self.assertTrue(success2)
        self.assertIsInstance(ticket2, Ticket)
        
        success3, ticket3 = Ticket.new(quantity=2, type='GENERAL', event=self.event, user=users[2])
        self.assertTrue(success3)
        self.assertIsInstance(ticket3, Ticket)
        
        # Intentar comprar una entrada más
        success, result = Ticket.new(
            quantity=1,
            type='GENERAL',
            event=self.event,
            user=self.user
        )
        
        # Verificar que es un error de evento lleno
        self.assertFalse(success)
        self.assertIsInstance(result, dict)
        if isinstance(result, dict):
            self.assertIn('event', result)
            self.assertEqual(
                result['event'],
                'Lo sentimos, este evento ya no tiene entradas disponibles'
            )

    def test_cannot_update_ticket_to_exceed_capacity(self):
        """Verifica que no se pueda actualizar un ticket para exceder la capacidad"""
        # Crear un ticket inicial con 4 entradas
        success, ticket = Ticket.new(quantity=4, type='GENERAL', event=self.event, user=self.user)
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
        # Crear múltiples usuarios usando método helper optimizado
        users = self._create_multiple_users(count=3)
        
        # Comprar entradas hasta llenar el evento
        success1, ticket1 = Ticket.new(quantity=4, type='GENERAL', event=self.event, user=users[0])
        self.assertTrue(success1)
        self.assertIsInstance(ticket1, Ticket)
        
        success2, ticket2 = Ticket.new(quantity=4, type='GENERAL', event=self.event, user=users[1])
        self.assertTrue(success2)
        self.assertIsInstance(ticket2, Ticket)
        
        success3, ticket3 = Ticket.new(quantity=2, type='GENERAL', event=self.event, user=users[2])
        self.assertTrue(success3)
        self.assertIsInstance(ticket3, Ticket)
        
        self.assertEqual(self.event.available_tickets(), 0)

    def test_multiple_tickets_respect_capacity(self):
        """Verifica que múltiples compras de tickets respeten la capacidad total"""
        # Crear múltiples usuarios usando método helper optimizado
        users = self._create_multiple_users(count=3)
        
        # Comprar entradas
        success1, ticket1 = Ticket.new(quantity=4, type='GENERAL', event=self.event, user=users[0])
        self.assertTrue(success1)
        self.assertIsInstance(ticket1, Ticket)
        
        success2, ticket2 = Ticket.new(quantity=4, type='GENERAL', event=self.event, user=users[1])
        self.assertTrue(success2)
        self.assertIsInstance(ticket2, Ticket)
        
        # Intentar comprar más entradas de las disponibles
        success, result = Ticket.new(
            quantity=3,
            type='GENERAL',
            event=self.event,
            user=users[2]
        )
        
        # Verificar que es un error de cantidad insuficiente
        self.assertFalse(success)
        self.assertIsInstance(result, dict)
        if isinstance(result, dict):
            self.assertIn('quantity', result)
            self.assertEqual(
                result['quantity'],
                'No hay suficientes entradas disponibles. Solo quedan 2 entradas.'
            )
