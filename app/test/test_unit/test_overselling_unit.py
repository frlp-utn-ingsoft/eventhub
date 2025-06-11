from django.test import TestCase
from app.models import User, Event, Venue, Ticket
from django.utils import timezone
from datetime import timedelta
from typing import Dict, Any, Union, Tuple, List

class TestOverselling(TestCase):
    def setUp(self):
        # Crear usuarios base para reutilizar en todos los tests
        self.user = self._create_test_user('testuser', 'testpass123')
        self.users = self._create_multiple_users(count=5, base_username='testuser')
        
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
        
        # Crear tickets base para diferentes escenarios
        # Ticket 1: 4 entradas (usuario 0)
        self.ticket1 = Ticket.objects.create(
            quantity=4,
            type='GENERAL',
            event=self.event,
            user=self.users[0]
        )
        
        # Ticket 2: 4 entradas (usuario 1) 
        self.ticket2 = Ticket.objects.create(
            quantity=4,
            type='GENERAL',
            event=self.event,
            user=self.users[1]
        )
        
        # Ticket 3: 2 entradas (usuario 2) - completa la capacidad
        self.ticket3 = Ticket.objects.create(
            quantity=2,
            type='GENERAL',
            event=self.event,
            user=self.users[2]
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
        # El evento ya está lleno con los tickets creados en setUp()
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
        # Usar el ticket1 creado en setUp() (4 entradas)
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
        # Los tickets ya están creados en setUp() y llenan la capacidad
        self.assertEqual(self.event.available_tickets(), 0)

    def test_multiple_tickets_respect_capacity(self):
        """Verifica que múltiples compras de tickets respeten la capacidad total"""
        # Crear un nuevo evento con capacidad disponible para este test específico
        new_event = Event.objects.create(
            title='New Test Event',
            description='New Test Description',
            scheduled_at=timezone.now() + timedelta(days=2),
            organizer=self.user,
            venue=self.venue
        )
        
        # Comprar entradas
        success1, ticket1 = Ticket.new(quantity=4, type='GENERAL', event=new_event, user=self.users[0])
        self.assertTrue(success1)
        self.assertIsInstance(ticket1, Ticket)
        
        success2, ticket2 = Ticket.new(quantity=4, type='GENERAL', event=new_event, user=self.users[1])
        self.assertTrue(success2)
        self.assertIsInstance(ticket2, Ticket)
        
        # Intentar comprar más entradas de las disponibles
        success, result = Ticket.new(
            quantity=3,
            type='GENERAL',
            event=new_event,
            user=self.users[2]
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
