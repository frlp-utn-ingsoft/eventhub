from django.test import TestCase, Client
from django.urls import reverse
from app.models import User, Event, Venue, Ticket
from django.utils import timezone
from datetime import timedelta

class TestOversellingIntegration(TestCase):
    def setUp(self):
        # Crear cliente de prueba
        self.client = Client()
        
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
            capacity=5,  # Capacidad de 5 personas
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
        
        # Loguear al usuario
        self.client.login(username='testuser', password='testpass123')

    def test_cannot_buy_tickets_when_event_is_full(self):
        """Verifica que no se puedan comprar entradas cuando el evento está lleno a través de la interfaz web"""
        # Primero llenamos el evento comprando todas las entradas disponibles
        response = self.client.post(
            reverse('buy_ticket', args=[self.event.id]),
            {
                'quantity': '5',
                'type': 'GENERAL',
                'card_number': '1234567890123456',
                'expiry': '12/25',
                'cvv': '123',
                'card_name': 'Test User',
                'terms': 'on'
            }
        )
        
        # Verificar que la primera compra fue exitosa
        self.assertEqual(response.status_code, 302)  # Redirección después de compra exitosa
        self.assertEqual(Ticket.objects.count(), 1)
        self.assertEqual(self.event.available_tickets(), 0)
        
        # Intentar comprar una entrada más cuando el evento está lleno
        response = self.client.post(
            reverse('buy_ticket', args=[self.event.id]),
            {
                'quantity': '1',
                'type': 'GENERAL',
                'card_number': '1234567890123456',
                'expiry': '12/25',
                'cvv': '123',
                'card_name': 'Test User',
                'terms': 'on'
            }
        )
        
        # Verificar que la segunda compra fue rechazada
        self.assertEqual(response.status_code, 200)  # Se muestra el formulario con error
        self.assertEqual(Ticket.objects.count(), 1)  # No se creó un nuevo ticket
        self.assertContains(response, "Lo sentimos, este evento ya no tiene entradas disponibles")

    def test_cannot_buy_more_tickets_than_available(self):
        """Verifica que no se puedan comprar más entradas que las disponibles a través de la interfaz web"""
        # Primero compramos 3 entradas
        response = self.client.post(
            reverse('buy_ticket', args=[self.event.id]),
            {
                'quantity': '3',
                'type': 'GENERAL',
                'card_number': '1234567890123456',
                'expiry': '12/25',
                'cvv': '123',
                'card_name': 'Test User',
                'terms': 'on'
            }
        )
        
        # Verificar que la primera compra fue exitosa
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Ticket.objects.count(), 1)
        self.assertEqual(self.event.available_tickets(), 2)
        
        # Intentar comprar 3 entradas más cuando solo quedan 2
        response = self.client.post(
            reverse('buy_ticket', args=[self.event.id]),
            {
                'quantity': '3',
                'type': 'GENERAL',
                'card_number': '1234567890123456',
                'expiry': '12/25',
                'cvv': '123',
                'card_name': 'Test User',
                'terms': 'on'
            }
        )
        
        # Verificar que la segunda compra fue rechazada
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Ticket.objects.count(), 1)
        self.assertContains(response, "No hay suficientes entradas disponibles. Solo quedan 2 entradas.")
