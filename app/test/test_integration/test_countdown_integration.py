from django.test import TestCase, Client
from django.urls import reverse
from app.models import User, Event, Venue
from django.utils import timezone
from datetime import timedelta


class CountdownIntegrationTest(TestCase):
    """Tests de integración para la funcionalidad de countdown"""
    
    def setUp(self):
        """Configuración inicial para los tests de integración"""
        self.client = Client()
        
        # Usuario regular (NO organizador)
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_organizer=False
        )
        
        # Usuario organizador
        self.organizer = User.objects.create_user(
            username='organizer',
            email='organizer@example.com',
            password='testpass123',
            is_organizer=True
        )
        
        # Venue para eventos
        self.venue = Venue.objects.create(
            name='Test Venue',
            adress='Test Address',
            city='Test City',
            capacity=100,
            contact='test@venue.com'
        )
        
        # Evento futuro para countdown
        self.future_event = Event.objects.create(
            title='Future Event',
            description='Event for countdown testing',
            scheduled_at=timezone.now() + timedelta(days=30),
            organizer=self.organizer,
            venue=self.venue
        )

        # Evento pasado para tests específicos
        self.past_event = Event.objects.create(
            title='Past Event',
            description='Event that already happened',
            scheduled_at=timezone.now() - timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue
        )

    def test_countdown_visible_for_non_organizer_user(self):
        """Test que el countdown es visible para usuarios no organizadores"""
        # Login como usuario regular
        self.client.login(username='testuser', password='testpass123')
        
        # Acceder al detalle del evento
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': self.future_event.id})
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el countdown está presente en el HTML
        self.assertContains(response, 'countdown-container')
        self.assertContains(response, 'countdown-timer')
        self.assertContains(response, 'Tiempo restante:')
        
        # Verificar que el JavaScript del countdown está presente
        self.assertContains(response, 'updateCountdown')

    def test_countdown_not_visible_for_organizer_user(self):
        """Test que el countdown NO es visible para usuarios organizadores"""
        # Login como organizador
        self.client.login(username='organizer', password='testpass123')
        
        # Acceder al detalle del evento
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': self.future_event.id})
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el countdown NO está presente
        self.assertNotContains(response, 'countdown-container')
        self.assertNotContains(response, 'countdown-timer')
        self.assertNotContains(response, 'Tiempo restante:')

    def test_countdown_context_variables(self):
        """Test que las variables de contexto para countdown son correctas"""
        # Login como usuario regular
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': self.future_event.id})
        )
        
        # Verificar variables de contexto
        self.assertEqual(response.context['event'], self.future_event)
        self.assertFalse(response.context['user_is_organizer'])
        
        # Login como organizador
        self.client.login(username='organizer', password='testpass123')
        
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': self.future_event.id})
        )
        
        # Para organizador, user_is_organizer debe ser True
        self.assertTrue(response.context['user_is_organizer'])

    def test_countdown_javascript_date_format(self):
        """Test que la fecha del evento se formatea correctamente para JavaScript"""
        # Login como usuario regular
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': self.future_event.id})
        )
        
        # Verificar que la fecha está en formato ISO para JavaScript
        content = response.content.decode('utf-8')
        
        # Buscar el formato de fecha ISO en el JavaScript (formato real)
        self.assertIn('const eventDateStr = "', content)
        self.assertIn('+00:00"', content)  # Timezone UTC
        
        # Verificar que el JavaScript tiene la función updateCountdown
        self.assertIn('function updateCountdown()', content)

    def test_countdown_for_multiple_events(self):
        """Test countdown para múltiples eventos"""
        # Crear otro evento futuro
        another_event = Event.objects.create(
            title='Another Future Event',
            description='Another event for testing',
            scheduled_at=timezone.now() + timedelta(days=45),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Login como usuario regular
        self.client.login(username='testuser', password='testpass123')
        
        # Verificar countdown en primer evento
        response1 = self.client.get(
            reverse('event_detail', kwargs={'event_id': self.future_event.id})
        )
        self.assertContains(response1, 'countdown-container')
        
        # Verificar countdown en segundo evento
        response2 = self.client.get(
            reverse('event_detail', kwargs={'event_id': another_event.id})
        )
        self.assertContains(response2, 'countdown-container')

    def test_countdown_with_past_event(self):
        """Test comportamiento del countdown con evento pasado usando evento del setUp"""
        # Login como usuario regular
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': self.past_event.id})
        )
        
        # El countdown debe estar presente (el JavaScript manejará el caso de evento pasado)
        self.assertContains(response, 'countdown-container')
        self.assertContains(response, 'updateCountdown')

    def test_countdown_authentication_required(self):
        """Test que se requiere autenticación para ver el countdown"""
        # Sin login
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': self.future_event.id})
        )
        
        # Debe redirigir al login
        self.assertEqual(response.status_code, 302)

    def test_countdown_with_invalid_event(self):
        """Test countdown con evento inexistente"""
        # Login como usuario regular
        self.client.login(username='testuser', password='testpass123')
        
        # Intentar acceder a evento inexistente
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': 99999})
        )
        
        # Debe retornar 404
        self.assertEqual(response.status_code, 404)

    def test_countdown_template_inheritance(self):
        """Test que el template del countdown hereda correctamente"""
        # Login como usuario regular
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': self.future_event.id})
        )
        
        # Verificar elementos comunes del template base
        self.assertContains(response, 'navbar')  # Navigation bar
        self.assertContains(response, 'container')     # Bootstrap container

    def test_countdown_responsive_design(self):
        """Test diseño responsive del countdown"""
        # Login como usuario regular
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': self.future_event.id})
        )
        
        # Verificar clases Bootstrap para responsive design
        self.assertContains(response, 'container')  # Container responsive
        self.assertContains(response, 'col-')       # Grid system 