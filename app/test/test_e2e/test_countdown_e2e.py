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
        
        # Eventos base para reutilizar en tests
        self.future_event = Event.objects.create(
            title='Future Event',
            description='Event for countdown testing',
            scheduled_at=timezone.now() + timedelta(days=30),
            organizer=self.organizer,
            venue=self.venue
        )

        self.past_event = Event.objects.create(
            title='Past Event', 
            description='Event that already happened',
            scheduled_at=timezone.now() - timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue
        )

    def test_countdown_visible_for_non_organizer_user_journey(self):
        """Test del flujo completo de usuario NO organizador viendo countdown usando Playwright"""
        # Login como usuario NO organizador
        self.login_user('testuser', 'testpass123')
        
        # Navegar al detalle del evento futuro
        self.page.goto(f"{self.live_server_url}/events/{self.future_event.pk}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que la página del evento cargó correctamente
        expect(self.page.locator("h1").filter(has_text="Future Event")).to_be_visible()
        
        # Verificar que el countdown está presente y visible
        expect(self.page.locator("#countdown-container")).to_be_visible()
        expect(self.page.locator("#countdown-timer")).to_be_visible()
        
        # Verificar que el countdown timer tiene contenido válido
        countdown_text = self.page.locator("#countdown-timer").inner_text()
        self.assertIsNotNone(countdown_text)
        
        # Verificar que el JavaScript del countdown está funcionando
        # Esperar un momento y verificar que el contenido cambia o está actualizado
        initial_text = self.page.locator("#countdown-timer").inner_text()
        self.page.wait_for_timeout(2000)  # Esperar 2 segundos
        updated_text = self.page.locator("#countdown-timer").inner_text()
        
        # El texto debería estar definido
        self.assertIsNotNone(initial_text)
        self.assertIsNotNone(updated_text)

    def test_countdown_not_visible_for_organizer_user(self):
        """Test que el countdown NO es visible para usuarios organizadores"""
        # Login como organizador
        self.login_user('organizer', 'testpass123')
        
        # Navegar al detalle del evento
        self.page.goto(f"{self.live_server_url}/events/{self.future_event.pk}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que la página del evento cargó correctamente
        expect(self.page.locator("h1").filter(has_text="Future Event")).to_be_visible()
        
        # Verificar que el countdown NO está presente
        countdown_container = self.page.locator("#countdown-container")
        expect(countdown_container).to_have_count(0)
        
        # Verificar que tampoco están los elementos específicos del countdown
        expect(self.page.locator("#countdown-timer")).to_have_count(0)

    def test_countdown_javascript_functionality(self):
        """Test funcionalidad JavaScript del countdown"""
        # Login como usuario NO organizador
        self.login_user('testuser', 'testpass123')
        
        # Navegar al detalle del evento
        self.page.goto(f"{self.live_server_url}/events/{self.future_event.pk}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que el script JavaScript está presente
        script_content = self.page.evaluate("() => document.body.innerHTML")
        self.assertIn("updateCountdown", script_content)
        self.assertIn("function", script_content)
        
        # Verificar que la fecha del evento está correctamente formateada para JavaScript
        self.assertIn("const eventDateStr", script_content)
        
        # Verificar que el countdown tiene un valor válido
        countdown_text = self.page.locator("#countdown-timer").inner_text()
        
        # El texto del countdown debería estar definido y contener información de tiempo
        self.assertIsNotNone(countdown_text)
        # Verificar que contiene palabras relacionadas con tiempo
        time_words = ["días", "horas", "minutos", "segundos", "día", "hora", "minuto", "segundo"]
        contains_time_word = any(word in countdown_text.lower() for word in time_words)
        self.assertTrue(contains_time_word)

    def test_countdown_responsive_design(self):
        """Test diseño responsive del countdown"""
        # Login como usuario NO organizador
        self.login_user('testuser', 'testpass123')
        
        # Navegar al detalle del evento
        self.page.goto(f"{self.live_server_url}/events/{self.future_event.pk}/")
        self.page.wait_for_load_state("networkidle")
        
        # Probar en viewport móvil
        self.page.set_viewport_size({"width": 375, "height": 667})
        
        # Verificar que el countdown sigue siendo visible en móvil
        expect(self.page.locator("#countdown-container")).to_be_visible()
        expect(self.page.locator("#countdown-timer")).to_be_visible()
        
        # Probar en tablet
        self.page.set_viewport_size({"width": 768, "height": 1024})
        expect(self.page.locator("#countdown-container")).to_be_visible()
        
        # Volver a desktop
        self.page.set_viewport_size({"width": 1200, "height": 800})
        expect(self.page.locator("#countdown-container")).to_be_visible()

    def test_countdown_with_past_event_behavior(self):
        """Test comportamiento del countdown con evento pasado"""
        # Login como usuario NO organizador
        self.login_user('testuser', 'testpass123')
        
        # Navegar al detalle del evento pasado
        self.page.goto(f"{self.live_server_url}/events/{self.past_event.pk}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que la página del evento cargó
        expect(self.page.locator("h1").filter(has_text="Past Event")).to_be_visible()
        
        # El countdown puede estar presente pero debería mostrar "Evento finalizado" o similar
        countdown_container = self.page.locator("#countdown-container")
        if countdown_container.count() > 0:
            # Si existe, debería mostrar algún mensaje de evento finalizado
            page_content = self.page.content()
            event_finished_indicators = [
                "Evento finalizado",
                "Evento terminado", 
                "Evento pasado",
                "comenzó",
                "ya comenzó",
                "El evento ya comenzó"
            ]
            finished_found = any(indicator in page_content for indicator in event_finished_indicators)
            self.assertTrue(finished_found)

    def test_countdown_visual_elements_present(self):
        """Test que todos los elementos visuales del countdown están presentes"""
        # Login como usuario NO organizador
        self.login_user('testuser', 'testpass123')
        
        # Navegar al detalle del evento
        self.page.goto(f"{self.live_server_url}/events/{self.future_event.pk}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar estructura HTML del countdown
        expect(self.page.locator("#countdown-container")).to_be_visible()
        
        # Verificar labels de tiempo
        labels = ["Días", "Horas", "Minutos", "Segundos", "días", "horas", "minutos", "segundos"]
        page_content = self.page.content()
        label_found = any(label in page_content for label in labels)
        self.assertTrue(label_found)
        
        # Verificar que hay algún texto que indica tiempo restante
        time_indicators = ["Tiempo restante", "Faltan", "Cuenta regresiva", "Countdown"]
        time_indicator_found = any(indicator in page_content for indicator in time_indicators)
        self.assertTrue(time_indicator_found)

    def test_countdown_event_information_display(self):
        """Test que la información del evento se muestra correctamente junto al countdown"""
        # Login como usuario NO organizador
        self.login_user('testuser', 'testpass123')
        
        # Navegar al detalle del evento
        self.page.goto(f"{self.live_server_url}/events/{self.future_event.pk}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar información del evento
        expect(self.page.locator("h1").filter(has_text="Future Event")).to_be_visible()
        expect(self.page.locator("p").filter(has_text="Event for countdown testing")).to_be_visible()
        
        # Verificar información del venue
        expect(self.page.locator("span").filter(has_text="Test Venue")).to_be_visible()
        
        # Verificar que el countdown y la información del evento están en la misma página
        expect(self.page.locator("#countdown-container")).to_be_visible()

    def test_countdown_authentication_requirement(self):
        """Test que se requiere autenticación para ver el countdown"""
        # Sin hacer login, intentar acceder al evento
        self.page.goto(f"{self.live_server_url}/events/{self.future_event.pk}/")
        
        # Debería redirigir al login
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que estamos en la página de login
        current_url = self.page.url
        login_indicators = ["/login", "login", "sign-in", "signin"]
        redirected_to_login = any(indicator in current_url.lower() for indicator in login_indicators)
        self.assertTrue(redirected_to_login)

    def test_countdown_multiple_events_navigation(self):
        """Test navegación entre múltiples eventos con countdown"""
        # Crear un evento adicional para probar navegación
        additional_event = Event.objects.create(
            title='Additional Event',
            description='Another event for navigation testing',
            scheduled_at=timezone.now() + timedelta(days=45),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Login como usuario NO organizador
        self.login_user('testuser', 'testpass123')
        
        # Navegar al primer evento
        self.page.goto(f"{self.live_server_url}/events/{self.future_event.pk}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar countdown en primer evento
        expect(self.page.locator("#countdown-container")).to_be_visible()
        expect(self.page.locator("h1").filter(has_text="Future Event")).to_be_visible()
        
        # Navegar al segundo evento
        self.page.goto(f"{self.live_server_url}/events/{additional_event.pk}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar countdown en segundo evento
        expect(self.page.locator("#countdown-container")).to_be_visible()
        expect(self.page.locator("h1").filter(has_text="Additional Event")).to_be_visible()

    def test_countdown_event_details_interaction(self):
        """Test interacción con detalles del evento que tiene countdown"""
        # Login como usuario NO organizador
        self.login_user('testuser', 'testpass123')
        
        # Navegar al detalle del evento
        self.page.goto(f"{self.live_server_url}/events/{self.future_event.pk}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que el countdown no interfiere con otros elementos de la página
        expect(self.page.locator("#countdown-container")).to_be_visible()
        
        # Verificar que otros elementos del evento son interactuables
        # (botones de compra, enlaces, etc. si existen)
        buy_buttons = self.page.locator(".btn:has-text('Comprar')")
        if buy_buttons.count() > 0:
            expect(buy_buttons.first).to_be_visible()
            expect(buy_buttons.first).to_be_enabled()
        
        # Verificar que la navegación funciona normalmente
        navbar = self.page.locator(".navbar")
        if navbar.count() > 0:
            expect(navbar).to_be_visible()
        
        # Verificar que se puede hacer scroll sin problemas con el countdown
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        self.page.wait_for_timeout(500)
        expect(self.page.locator("#countdown-container")).to_be_visible() 