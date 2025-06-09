from django.utils import timezone
import datetime
from playwright.sync_api import expect

from app.models import User, Event, Venue, Category, Ticket, RefundRequest
from app.test.test_e2e.base import BaseE2ETest

class RefundValidationE2ETest(BaseE2ETest):
    """Tests end-to-end para la validación de solicitudes de reembolso"""

    def setUp(self):
        super().setUp()
        
        # Limpiar la base de datos antes de cada test
        RefundRequest.objects.all().delete()
        Ticket.objects.all().delete()
        Event.objects.all().delete()
        User.objects.all().delete()
        Venue.objects.all().delete()
        Category.objects.all().delete()

        # Crear usuario
        self.user = User.objects.create_user(
            username="usuario_test",
            email="usuario@test.com",
            password="password123"
        )

        # Crear venue y categoría
        self.venue = Venue.objects.create(
            name="Venue de prueba",
            adress="Dirección de prueba",
            city="Ciudad de prueba",
            capacity=100,
            contact="contacto@prueba.com"
        )

        self.category = Category.objects.create(
            name="Categoría de prueba",
            description="Descripción de la categoría de prueba",
            is_active=True
        )

        # Crear evento
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.user,
            venue=self.venue,
            category=self.category
        )

        # Crear ticket
        self.ticket = Ticket.objects.create(
            user=self.user,
            event=self.event,
            quantity=1,
            type="REGULAR"
        )

    def test_cannot_have_multiple_active_refund_requests(self):
        """Test que verifica que un usuario no puede tener múltiples solicitudes de reembolso activas"""
        # Iniciar sesión
        self.login_user("usuario_test", "password123")
        
        # Ir a la página de tickets
        self.page.goto(f"{self.live_server_url}/tickets/")
        
        # Esperar a que la tabla se cargue
        self.page.wait_for_selector("table tbody tr")
        
        # Verificar que el ticket está visible
        ticket_row = self.page.locator("table tbody tr").filter(has_text="Evento de prueba")
        expect(ticket_row).to_be_visible()
        
        # Hacer clic en el botón de ver detalles
        detail_button = ticket_row.locator("a.btn-outline-primary")
        expect(detail_button).to_be_visible()
        detail_button.click()
        
        # Esperar a que la página de detalles se cargue
        self.page.wait_for_selector("h1")
        
        # Verificar que el botón de reembolso está visible
        refund_button = self.page.locator("a.btn-outline-danger")
        expect(refund_button).to_be_visible()
        
        # Crear primera solicitud de reembolso
        refund_button.click()
        
        # Esperar a que el formulario se cargue
        self.page.wait_for_selector("form")
        
        # Llenar el formulario
        self.page.get_by_label("Motivo del reembolso").select_option("unable_to_attend")
        self.page.get_by_label("Detalles adicionales").fill("Primera solicitud de reembolso")
        self.page.get_by_label("Entiendo y acepto la política de reembolsos").check()
        
        # Enviar el formulario
        self.page.get_by_role("button", name="Enviar Solicitud").click()
        
        # Verificar que se redirige a la página de tickets
        expect(self.page).to_have_url(f"{self.live_server_url}/tickets/")
        
        # Volver a la página de detalles del ticket
        detail_button = self.page.locator("a.btn-outline-primary").first
        detail_button.click()
        
        # Intentar crear una segunda solicitud
        refund_button = self.page.locator("a.btn-outline-danger")
        expect(refund_button).to_be_visible()
        refund_button.click()
        
        # Esperar a que el formulario se cargue
        self.page.wait_for_selector("form")
        
        # Llenar el formulario
        self.page.get_by_label("Motivo del reembolso").select_option("unable_to_attend")
        self.page.get_by_label("Detalles adicionales").fill("Segunda solicitud de reembolso")
        self.page.get_by_label("Entiendo y acepto la política de reembolsos").check()
        
        # Enviar el formulario
        self.page.get_by_role("button", name="Enviar Solicitud").click()
        
        # Verificar en la base de datos que solo hay una solicitud activa
        active_refunds = RefundRequest.objects.filter(
            user=self.user,
            ticket_code=self.ticket.ticket_code,
            approval__isnull=True
        ).count()
        self.assertEqual(active_refunds, 1) 