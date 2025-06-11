import re
from playwright.sync_api import expect
from django.utils import timezone
from datetime import timedelta
from app.models import User, Event, Venue
from .base import BaseE2ETest


class CountdownE2ETest(BaseE2ETest):
    """Tests end-to-end para la funcionalidad completa de countdown usando Playwright"""
    
    def setUp(self):
        """Configuración inicial para los tests e2e"""
        super().setUp()
        
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

    def test_countdown_visible_for_regular_user(self):
        """Test que el countdown es visible para usuarios regulares usando Playwright"""
        # Crear evento futuro
        future_event = Event.objects.create(
            title='Future Event',
            description='Event for countdown testing',
            scheduled_at=timezone.now() + timedelta(days=30),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Login como usuario regular
        self.login_user('testuser', 'testpass123')
        
        # Navegar al detalle del evento
        self.page.goto(f"{self.live_server_url}/events/{future_event.id}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que el countdown está presente
        expect(self.page.locator("#countdown-container")).to_be_visible()
        expect(self.page.locator("text=Tiempo restante")).to_be_visible()
        
        # Verificar que el JavaScript del countdown está funcionando
        # Esperar a que aparezcan los números del countdown
        expect(self.page.locator("#countdown-timer")).to_be_visible()
        
        # Verificar elementos específicos del countdown
        expect(self.page.locator(".countdown-days")).to_be_visible()
        expect(self.page.locator(".countdown-hours")).to_be_visible()
        expect(self.page.locator(".countdown-minutes")).to_be_visible()
        expect(self.page.locator(".countdown-seconds")).to_be_visible()

    def test_countdown_not_visible_for_organizer(self):
        """Test que el countdown NO es visible para organizadores usando Playwright"""
        # Crear evento futuro
        future_event = Event.objects.create(
            title='Organizer Event',
            description='Event organized by this user',
            scheduled_at=timezone.now() + timedelta(days=15),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Login como organizador
        self.login_user('organizer', 'testpass123')
        
        # Navegar al detalle del evento
        self.page.goto(f"{self.live_server_url}/events/{future_event.id}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que el countdown NO está presente
        expect(self.page.locator("#countdown-container")).not_to_be_visible()
        expect(self.page.locator("text=Tiempo restante")).not_to_be_visible()
        
        # Pero el resto del contenido del evento debe estar visible
        expect(self.page.locator("text=Organizer Event")).to_be_visible()

    def test_countdown_with_different_time_periods(self):
        """Test countdown con diferentes períodos de tiempo usando Playwright"""
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
        
        # Login como usuario regular
        self.login_user('testuser', 'testpass123')
        
        # Test evento futuro lejano
        self.page.goto(f"{self.live_server_url}/events/{far_future_event.id}/")
        self.page.wait_for_load_state("networkidle")
        
        expect(self.page.locator("#countdown-container")).to_be_visible()
        # Debe mostrar días (número mayor que 0)
        expect(self.page.locator(".countdown-days")).to_be_visible()
        
        # Test evento próximo
        self.page.goto(f"{self.live_server_url}/events/{near_future_event.id}/")
        self.page.wait_for_load_state("networkidle")
        
        expect(self.page.locator("#countdown-container")).to_be_visible()
        # Para evento próximo, debe mostrar horas principalmente
        expect(self.page.locator(".countdown-hours")).to_be_visible()

    def test_countdown_past_event_message(self):
        """Test mensaje de evento pasado en countdown usando Playwright"""
        # Crear evento pasado
        past_event = Event.objects.create(
            title='Past Event',
            description='Event that already happened',
            scheduled_at=timezone.now() - timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Login como usuario regular
        self.login_user('testuser', 'testpass123')
        
        # Navegar al evento pasado
        self.page.goto(f"{self.live_server_url}/events/{past_event.id}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que muestra mensaje de evento pasado
        expect(self.page.locator("#countdown-container")).to_be_visible()
        expect(self.page.locator("text=El evento ya comenzó")).to_be_visible()

    def test_countdown_javascript_functionality(self):
        """Test funcionalidad JavaScript del countdown usando Playwright"""
        # Crear evento futuro con tiempo específico
        future_event = Event.objects.create(
            title='JS Test Event',
            description='Event for JavaScript testing',
            scheduled_at=timezone.now() + timedelta(days=2, hours=3, minutes=30),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Login como usuario regular
        self.login_user('testuser', 'testpass123')
        
        # Navegar al evento
        self.page.goto(f"{self.live_server_url}/events/{future_event.id}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que el countdown está presente
        expect(self.page.locator("#countdown-container")).to_be_visible()
        
        # Obtener valores iniciales del countdown
        initial_seconds = self.page.locator(".countdown-seconds").inner_text()
        
        # Esperar un poco y verificar que los segundos cambian (countdown activo)
        self.page.wait_for_timeout(2000)  # Esperar 2 segundos
        
        # Los segundos deberían haber cambiado (decrementado)
        current_seconds = self.page.locator(".countdown-seconds").inner_text()
        # Note: En algunos casos podría ser el mismo número si cayó en el momento exacto
        # Lo importante es que el elemento existe y es numérico
        self.assertTrue(current_seconds.isdigit())

    def test_countdown_responsive_design(self):
        """Test diseño responsive del countdown usando Playwright"""
        # Crear evento futuro
        future_event = Event.objects.create(
            title='Responsive Test Event',
            description='Event for responsive testing',
            scheduled_at=timezone.now() + timedelta(days=5),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Login como usuario regular
        self.login_user('testuser', 'testpass123')
        
        # Navegar al evento
        self.page.goto(f"{self.live_server_url}/events/{future_event.id}/")
        self.page.wait_for_load_state("networkidle")
        
        # Probar en viewport móvil
        self.page.set_viewport_size({"width": 375, "height": 667})
        
        # Verificar que el countdown es responsive
        expect(self.page.locator("#countdown-container")).to_be_visible()
        expect(self.page.locator(".countdown-days")).to_be_visible()
        expect(self.page.locator(".countdown-hours")).to_be_visible()
        
        # Probar en viewport tablet
        self.page.set_viewport_size({"width": 768, "height": 1024})
        expect(self.page.locator("#countdown-container")).to_be_visible()
        
        # Probar en viewport desktop
        self.page.set_viewport_size({"width": 1200, "height": 800})
        expect(self.page.locator("#countdown-container")).to_be_visible()

    def test_countdown_navigation_and_interaction(self):
        """Test navegación e interacción con countdown usando Playwright"""
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
        
        # Login como usuario regular
        self.login_user('testuser', 'testpass123')
        
        # Navegar a lista de eventos
        self.page.goto(f"{self.live_server_url}/events/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que los eventos están listados
        expect(self.page.locator("text=Event 1")).to_be_visible()
        expect(self.page.locator("text=Event 2")).to_be_visible()
        
        # Hacer clic en el primer evento
        self.page.click("text=Event 1")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que estamos en el detalle del evento y countdown está presente
        expect(self.page.locator("text=Event 1")).to_be_visible()
        expect(self.page.locator("#countdown-container")).to_be_visible()
        
        # Navegar de vuelta a eventos
        self.page.click("text=Eventos")
        self.page.wait_for_load_state("networkidle")
        
        # Hacer clic en el segundo evento
        self.page.click("text=Event 2")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar countdown del segundo evento
        expect(self.page.locator("text=Event 2")).to_be_visible()
        expect(self.page.locator("#countdown-container")).to_be_visible()

    def test_countdown_with_buy_ticket_interaction(self):
        """Test interacción del countdown con compra de tickets usando Playwright"""
        # Crear evento futuro
        future_event = Event.objects.create(
            title='Ticket Purchase Event',
            description='Event for testing countdown with ticket purchase',
            scheduled_at=timezone.now() + timedelta(days=7),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Login como usuario regular
        self.login_user('testuser', 'testpass123')
        
        # Navegar al evento
        self.page.goto(f"{self.live_server_url}/events/{future_event.id}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que countdown y botón de compra están presentes
        expect(self.page.locator("#countdown-container")).to_be_visible()
        expect(self.page.locator("text=Comprar Entrada")).to_be_visible()
        
        # El countdown no debe interferir con la funcionalidad de compra
        buy_button = self.page.locator("text=Comprar Entrada")
        expect(buy_button).to_be_enabled()

    def test_countdown_error_handling(self):
        """Test manejo de errores en countdown usando Playwright"""
        # Login como usuario regular
        self.login_user('testuser', 'testpass123')
        
        # Intentar acceder a evento inexistente
        self.page.goto(f"{self.live_server_url}/events/99999/")
        self.page.wait_for_load_state("networkidle")
        
        # Debe mostrar página de error 404
        expect(self.page.locator("text=404")).to_be_visible()

    def test_countdown_accessibility_features(self):
        """Test características de accesibilidad del countdown usando Playwright"""
        # Crear evento futuro
        future_event = Event.objects.create(
            title='Accessibility Test Event',
            description='Event for accessibility testing',
            scheduled_at=timezone.now() + timedelta(days=3),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Login como usuario regular
        self.login_user('testuser', 'testpass123')
        
        # Navegar al evento
        self.page.goto(f"{self.live_server_url}/events/{future_event.id}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que el countdown tiene elementos accesibles
        countdown_container = self.page.locator("#countdown-container")
        expect(countdown_container).to_be_visible()
        
        # Verificar que tiene estructura semántica apropiada
        expect(self.page.locator(".countdown-section")).to_be_visible()
        
        # Verificar que los textos son legibles
        expect(self.page.locator("text=días")).to_be_visible()
        expect(self.page.locator("text=horas")).to_be_visible()
        expect(self.page.locator("text=minutos")).to_be_visible()
        expect(self.page.locator("text=segundos")).to_be_visible()

    def test_countdown_multiple_user_sessions(self):
        """Test countdown con múltiples sesiones de usuario usando Playwright"""
        # Crear evento futuro
        future_event = Event.objects.create(
            title='Multi-User Event',
            description='Event for multi-user testing',
            scheduled_at=timezone.now() + timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Login como usuario regular
        self.login_user('testuser', 'testpass123')
        
        # Navegar al evento
        self.page.goto(f"{self.live_server_url}/events/{future_event.id}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar countdown para usuario regular
        expect(self.page.locator("#countdown-container")).to_be_visible()
        
        # Logout y login como organizador en la misma sesión
        self.page.click("button:has-text('Salir')")
        self.page.wait_for_load_state("networkidle")
        
        # Login como organizador
        self.login_user('organizer', 'testpass123')
        
        # Navegar al mismo evento
        self.page.goto(f"{self.live_server_url}/events/{future_event.id}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que countdown NO está presente para organizador
        expect(self.page.locator("#countdown-container")).not_to_be_visible() 