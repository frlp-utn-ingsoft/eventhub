from django.utils import timezone
from datetime import timedelta
from playwright.sync_api import expect

from app.models import Event, User
from app.test.test_e2e.base import BaseE2ETest


class EventToggleTest(BaseE2ETest):
    """Tests E2E para el toggle de eventos pasados"""

    def setUp(self):
        super().setUp()

        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )

        # Crear usuario regular
        self.regular_user = User.objects.create_user(
            username="usuario",
            email="usuario@example.com",
            password="password123",
            is_organizer=False,
        )

        # Crear eventos de prueba usando fechas relativas a now()
        now = timezone.now()
        
        # Evento futuro (1 mes adelante)
        event_date1 = now + timedelta(days=30)
        self.event1 = Event.objects.create(
            title="Evento de prueba 1",
            description="Descripción del evento 1",
            scheduled_at=event_date1,
            organizer=self.organizer,
        )

        # Evento pasado (1 día atrás)
        event_date2 = now - timedelta(days=1)
        self.event2 = Event.objects.create(
            title="Evento pasado",
            description="Descripción del evento pasado",
            scheduled_at=event_date2,
            organizer=self.organizer,
        )

    def test_events_past_toggle(self):
        """Test que verifica el funcionamiento del toggle para mostrar eventos pasados"""
        # Iniciar sesión como usuario regular
        self.login_user("usuario", "password123")
        
        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")
        
        # Esperar a que la página cargue completamente
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que el toggle existe y está desactivado por defecto
        toggle = self.page.locator("#showPastEvents")
        expect(toggle).to_be_visible()
        expect(toggle).not_to_be_checked()
        
        # Verificar que solo se muestra el evento futuro
        future_event = self.page.locator("table tbody tr").filter(has_text="Evento de prueba 1")
        expect(future_event).to_be_visible()
        
        past_event = self.page.locator("table tbody tr").filter(has_text="Evento pasado")
        expect(past_event).not_to_be_visible()
        
        # Activar el toggle
        toggle.click()
        
        # Esperar a que la página cargue completamente después del cambio
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que ahora se muestran ambos eventos
        expect(future_event).to_be_visible()
        expect(past_event).to_be_visible()
        
        # Verificar que el toggle está activado
        expect(toggle).to_be_checked()
        
        # Verificar el orden de los eventos (futuro antes que pasado)
        rows = self.page.locator("table tbody tr")
        future_index = rows.evaluate_all("(rows) => rows.findIndex(row => row.textContent.includes('Evento de prueba 1'))")
        past_index = rows.evaluate_all("(rows) => rows.findIndex(row => row.textContent.includes('Evento pasado'))")
        assert future_index < past_index, "El evento futuro debería aparecer antes que el evento pasado"
        
        # Desactivar el toggle
        toggle.click()
        
        # Esperar a que la página cargue completamente después del cambio
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que solo se muestra el evento futuro nuevamente
        expect(future_event).to_be_visible()
        expect(past_event).not_to_be_visible()
        
        # Verificar que el toggle está desactivado
        expect(toggle).not_to_be_checked() 