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
        self.page.goto(f"{self.live_server_url}/events/{future_event.pk}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que el countdown está presente (elementos reales)
        expect(self.page.locator("#countdown-container")).to_be_visible()
        expect(self.page.locator("text=Tiempo restante")).to_be_visible()
        
        # Verificar que el JavaScript del countdown está funcionando
        expect(self.page.locator("#countdown-timer")).to_be_visible()

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
        self.page.goto(f"{self.live_server_url}/events/{future_event.pk}/")
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
        
        # Login como usuario regular
        self.login_user('testuser', 'testpass123')
        
        # Test evento futuro lejano
        self.page.goto(f"{self.live_server_url}/events/{far_future_event.pk}/")
        self.page.wait_for_load_state("networkidle")
        
        expect(self.page.locator("#countdown-container")).to_be_visible()
        # Verificar que el timer está presente y funcionando
        expect(self.page.locator("#countdown-timer")).to_be_visible()

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
        self.page.goto(f"{self.live_server_url}/events/{past_event.pk}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que el countdown container está presente
        expect(self.page.locator("#countdown-container")).to_be_visible()
        # Para eventos pasados, el timer debería mostrar mensaje apropiado
        expect(self.page.locator("#countdown-timer")).to_be_visible()

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
        self.page.goto(f"{self.live_server_url}/events/{future_event.pk}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que el countdown está presente
        expect(self.page.locator("#countdown-container")).to_be_visible()
        
        # Verificar que el timer tiene contenido
        timer_element = self.page.locator("#countdown-timer")
        expect(timer_element).to_be_visible()
        
        # Esperar un poco para que el JavaScript se ejecute
        self.page.wait_for_timeout(2000)
        
        # Verificar que el timer tiene algún contenido (countdown o mensaje)
        timer_text = timer_element.inner_text()
        self.assertTrue(len(timer_text) > 0)

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
        self.page.goto(f"{self.live_server_url}/events/{future_event.pk}/")
        self.page.wait_for_load_state("networkidle")
        
        # Probar en viewport móvil
        self.page.set_viewport_size({"width": 375, "height": 667})
        
        # Verificar que el countdown es responsive
        expect(self.page.locator("#countdown-container")).to_be_visible()
        expect(self.page.locator("#countdown-timer")).to_be_visible()
        
        # Probar en viewport tablet
        self.page.set_viewport_size({"width": 768, "height": 1024})
        expect(self.page.locator("#countdown-container")).to_be_visible()
        
        # Probar en viewport desktop
        self.page.set_viewport_size({"width": 1200, "height": 800})
        expect(self.page.locator("#countdown-container")).to_be_visible()

    def test_countdown_navigation_and_interaction(self):
        """Test navegación e interacción con countdown usando Playwright"""
        # Crear evento
        event1 = Event.objects.create(
            title='Event 1',
            description='First event',
            scheduled_at=timezone.now() + timedelta(days=10),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Login como usuario regular
        self.login_user('testuser', 'testpass123')
        
        # Navegar a lista de eventos
        self.page.goto(f"{self.live_server_url}/events/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que el evento está listado
        expect(self.page.locator("text=Event 1")).to_be_visible()
        
        # Hacer clic en el evento (usando link específico)
        self.page.click(f"a[href='/events/{event1.pk}/']")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que estamos en el detalle del evento y countdown está presente
        expect(self.page.locator("text=Event 1")).to_be_visible()
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
        self.page.goto(f"{self.live_server_url}/events/{future_event.pk}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que countdown y botón de compra están presentes
        expect(self.page.locator("#countdown-container")).to_be_visible()
        expect(self.page.locator("text=Comprar Entrada")).to_be_visible()
        
        # El countdown no debe interferir con la funcionalidad de compra
        buy_button = self.page.locator("text=Comprar Entrada")
        expect(buy_button).to_be_enabled()

    def test_countdown_event_information_display(self):
        """Test que verifica la información del evento junto con el countdown"""
        # Crear evento futuro
        future_event = Event.objects.create(
            title='Info Display Event',
            description='Event for testing information display',
            scheduled_at=timezone.now() + timedelta(days=3),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Login como usuario regular
        self.login_user('testuser', 'testpass123')
        
        # Navegar al evento
        self.page.goto(f"{self.live_server_url}/events/{future_event.pk}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar información del evento
        expect(self.page.locator("text=Info Display Event")).to_be_visible()
        expect(self.page.locator("text=Test Venue")).to_be_visible()
        expect(self.page.locator("text=100 personas")).to_be_visible()  # Capacidad
        
        # Verificar que countdown está presente para usuario no organizador
        expect(self.page.locator("#countdown-container")).to_be_visible()
        expect(self.page.locator("#countdown-timer")).to_be_visible()

    def test_countdown_alert_styling(self):
        """Test que verifica el estilo del countdown (Bootstrap alert)"""
        # Crear evento futuro
        future_event = Event.objects.create(
            title='Styling Test Event',
            description='Event for testing countdown styling',
            scheduled_at=timezone.now() + timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Login como usuario regular
        self.login_user('testuser', 'testpass123')
        
        # Navegar al evento
        self.page.goto(f"{self.live_server_url}/events/{future_event.pk}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que countdown tiene clases de Bootstrap
        countdown_container = self.page.locator("#countdown-container")
        expect(countdown_container).to_be_visible()
        expect(countdown_container).to_have_class(re.compile(r".*alert.*"))  # Bootstrap alert class 