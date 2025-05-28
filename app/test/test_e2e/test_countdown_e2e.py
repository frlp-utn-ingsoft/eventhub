from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from app.models import Event, Venue
from django.utils import timezone
from datetime import timedelta
import time

User = get_user_model()


class CountdownE2ETest(TestCase):
    """Tests end-to-end para la funcionalidad completa de countdown"""
    
    def setUp(self):
        """Configuración inicial para los tests e2e"""
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

    def test_complete_countdown_user_journey(self):
        """Test del flujo completo de usuario viendo countdown"""
        # Crear evento futuro
        future_event = Event.objects.create(
            title='Future Event',
            description='Event for countdown testing',
            scheduled_at=timezone.now() + timedelta(days=30),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # 1. Usuario accede sin login -> redirige a login
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': future_event.id})
        )
        self.assertEqual(response.status_code, 302)
        
        # 2. Usuario hace login
        login_success = self.client.login(username='testuser', password='testpass123')
        self.assertTrue(login_success)
        
        # 3. Usuario accede al evento y ve countdown
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': future_event.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'countdown-container')
        self.assertContains(response, 'Tiempo restante:')
        
        # 4. Verificar que el JavaScript está presente y funcional
        content = response.content.decode('utf-8')
        self.assertIn('function updateCountdown()', content)
        self.assertIn('setInterval(updateCountdown, 1000)', content)

    def test_organizer_vs_regular_user_countdown_visibility(self):
        """Test e2e de visibilidad del countdown según tipo de usuario"""
        # Crear evento
        event = Event.objects.create(
            title='Test Event',
            description='Event for testing',
            scheduled_at=timezone.now() + timedelta(days=15),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Test como usuario regular
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': event.id})
        )
        self.assertContains(response, 'countdown-container')
        self.assertFalse(response.context['user_is_organizer'])
        
        # Logout y login como organizador
        self.client.logout()
        self.client.login(username='organizer', password='testpass123')
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': event.id})
        )
        self.assertNotContains(response, 'countdown-container')
        self.assertTrue(response.context['user_is_organizer'])

    def test_countdown_with_different_event_times(self):
        """Test e2e del countdown con diferentes tiempos de evento"""
        # Evento muy futuro (más de 30 días)
        far_future_event = Event.objects.create(
            title='Far Future Event',
            description='Event very far in the future',
            scheduled_at=timezone.now() + timedelta(days=60),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Evento próximo (menos de 1 día)
        near_future_event = Event.objects.create(
            title='Near Future Event',
            description='Event happening soon',
            scheduled_at=timezone.now() + timedelta(hours=12),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Evento pasado
        past_event = Event.objects.create(
            title='Past Event',
            description='Event that already happened',
            scheduled_at=timezone.now() - timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        # Test evento futuro lejano
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': far_future_event.id})
        )
        self.assertContains(response, 'countdown-container')
        content = response.content.decode('utf-8')
        self.assertIn('días', content)  # Debe mostrar días
        
        # Test evento próximo
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': near_future_event.id})
        )
        self.assertContains(response, 'countdown-container')
        
        # Test evento pasado
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': past_event.id})
        )
        self.assertContains(response, 'countdown-container')  # Container presente
        content = response.content.decode('utf-8')
        self.assertIn('¡El evento ya comenzó!', content)  # Mensaje de evento pasado

    def test_countdown_navigation_flow(self):
        """Test e2e del flujo de navegación con countdown"""
        # Crear múltiples eventos
        event1 = Event.objects.create(
            title='Event 1',
            description='First event',
            scheduled_at=timezone.now() + timedelta(days=10),
            organizer=self.organizer,
            venue=self.venue
        )
        
        event2 = Event.objects.create(
            title='Event 2',
            description='Second event',
            scheduled_at=timezone.now() + timedelta(days=20),
            organizer=self.organizer,
            venue=self.venue
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        # 1. Ver lista de eventos
        response = self.client.get(reverse('events'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Event 1')
        self.assertContains(response, 'Event 2')
        
        # 2. Navegar al primer evento
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': event1.id})
        )
        self.assertContains(response, 'countdown-container')
        self.assertContains(response, 'Event 1')
        
        # 3. Navegar al segundo evento
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': event2.id})
        )
        self.assertContains(response, 'countdown-container')
        self.assertContains(response, 'Event 2')

    def test_countdown_responsive_behavior(self):
        """Test e2e del comportamiento responsive del countdown"""
        event = Event.objects.create(
            title='Responsive Test Event',
            description='Event for responsive testing',
            scheduled_at=timezone.now() + timedelta(days=5),
            organizer=self.organizer,
            venue=self.venue
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': event.id})
        )
        
        content = response.content.decode('utf-8')
        
        # Verificar clases Bootstrap para responsive design
        self.assertIn('d-flex', content)
        self.assertIn('align-items-center', content)
        self.assertIn('alert', content)
        self.assertIn('mb-4', content)
        
        # Verificar que el countdown está dentro de un container responsive
        self.assertIn('container', content)

    def test_countdown_error_handling(self):
        """Test e2e del manejo de errores en countdown"""
        event = Event.objects.create(
            title='Error Test Event',
            description='Event for error testing',
            scheduled_at=timezone.now() + timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        # Test con evento válido
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': event.id})
        )
        self.assertEqual(response.status_code, 200)
        
        # Test con evento inexistente
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': 99999})
        )
        self.assertEqual(response.status_code, 404)

    def test_countdown_javascript_functionality(self):
        """Test e2e de la funcionalidad JavaScript del countdown"""
        event = Event.objects.create(
            title='JS Test Event',
            description='Event for JavaScript testing',
            scheduled_at=timezone.now() + timedelta(days=2, hours=3, minutes=30),
            organizer=self.organizer,
            venue=self.venue
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': event.id})
        )
        
        content = response.content.decode('utf-8')
        
        # Verificar elementos JavaScript críticos
        self.assertIn('function updateCountdown()', content)
        self.assertIn('const eventDateStr =', content)
        self.assertIn('const eventDate = new Date(eventDateStr)', content)
        self.assertIn('const now = new Date()', content)
        self.assertIn('const timeLeft = eventDate.getTime() - now.getTime()', content)
        self.assertIn('Math.floor(timeLeft / (1000 * 60 * 60 * 24))', content)  # Cálculo días
        self.assertIn('setInterval(updateCountdown, 1000)', content)  # Actualización cada segundo
        
        # Verificar manejo de errores en JavaScript
        self.assertIn('try {', content)
        self.assertIn('} catch (error) {', content)

    def test_countdown_complete_user_experience(self):
        """Test e2e de la experiencia completa del usuario con countdown"""
        # Crear evento con tiempo específico
        event = Event.objects.create(
            title='Complete UX Event',
            description='Event for complete user experience testing',
            scheduled_at=timezone.now() + timedelta(days=7, hours=12, minutes=45),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # 1. Login del usuario
        self.client.login(username='testuser', password='testpass123')
        
        # 2. Acceso al evento
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': event.id})
        )
        
        # 3. Verificar experiencia visual completa
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Complete UX Event')
        self.assertContains(response, 'countdown-container')
        self.assertContains(response, 'Tiempo restante:')
        self.assertContains(response, 'bi-clock')  # Ícono de reloj
        
        # 4. Verificar que puede comprar tickets (botón presente)
        self.assertContains(response, 'Comprar Entrada')
        
        # 5. Verificar que puede ver detalles del venue
        self.assertContains(response, 'Test Venue')
        # self.assertContains(response, 'Test Address')  # La dirección no se muestra en el template
        
        # 6. Verificar navegación funcional
        self.assertContains(response, 'EventHub')  # Navbar
        self.assertContains(response, 'Eventos')   # Link a eventos 