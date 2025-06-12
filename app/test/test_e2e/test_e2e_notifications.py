from datetime import timedelta
from django.utils import timezone
from playwright.sync_api import expect
from app.models import Event, User, Venue, Ticket
from app.test.test_e2e.base import BaseE2ETest

class NotificacionesCambioEventoE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()
        self.organizer = User.objects.create_user(username='e2euser', password='1234', is_organizer=True)
        self.venue = Venue.objects.create(
            name="Test Venue",
            address="Calle Falsa",
            city="Ciudad",
            capacity=100,
            contact_info="info@test.com",
            created_by=self.organizer
        )
        self.new_venue = Venue.objects.create(
            name="New Venue",
            address="Avenida Siempre Viva",
            city="Otra Ciudad",
            capacity=200,
            contact_info="info@newvenue.com",
            created_by=self.organizer
        )
        self.event = Event.objects.create(
            title="Evento de Prueba",
            description="Descripción original del evento.",
            scheduled_at=timezone.now() + timedelta(days=7),
            organizer=self.organizer,
            venue=self.venue
        )
        self.client_user = User.objects.create_user(username='clientuser', password='1234')
        Ticket.objects.create(
            user=self.client_user,
            event=self.event,
            type="GENERAL",
            quantity=1,
            price_paid=50.00
        )

    def test_notificacion_aparece_cuando_evento_cambia(self):
        # --- PASO 1: Login como Organizador ---
        self.page.goto(f"{self.live_server_url}/accounts/login/")
        self.page.get_by_placeholder("Ingresá tu usuario").fill(self.organizer.username)
        self.page.get_by_placeholder("Ingresá tu contraseña").fill("1234")
        self.page.get_by_role("button", name="Iniciar sesión").click()
        expect(self.page.get_by_role("button", name="Salir")).to_be_visible()

        # --- PASO 2: Editar el evento ---
        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/edit/")
        expect(self.page.locator('input[name="title"]')).to_be_visible()
        
        self.page.locator('input[name="title"]').fill('Evento de Prueba Editado')
        self.page.locator('textarea[name="description"]').fill('Esta es la nueva descripción del evento editado.')
        nueva_fecha = (timezone.now() + timedelta(days=10)).strftime("%Y-%m-%dT%H:%M")
        self.page.locator('input[name="scheduled_at"]').fill(nueva_fecha)
        self.page.locator('select[name="venue"]').select_option(label=self.new_venue.name)
        self.page.get_by_role('button', name='Guardar Cambios').click()
        
        # Esperamos la redirección a la página del evento específico
        self.page.wait_for_url(f"{self.live_server_url}/events/")
        
        # --- PASO 3: Logout y Login como Cliente ---
        expect(self.page.get_by_role("button", name="Salir")).to_be_visible()
        self.page.get_by_role("button", name="Salir").click()
        self.page.wait_for_url(f"{self.live_server_url}/accounts/login/")
        
        self.page.get_by_placeholder("Ingresá tu usuario").fill(self.client_user.username)
        self.page.get_by_placeholder("Ingresá tu contraseña").fill("1234")
        self.page.get_by_role("button", name="Iniciar sesión").click()
        expect(self.page.get_by_role("button", name="Salir")).to_be_visible()

        # --- PASO 4: Verificar la Notificación ---
        self.page.goto(f"{self.live_server_url}/notifications/")
        
        expect(self.page.get_by_text("Tus Notificaciones")).to_be_visible(timeout=10000)
        
        # **CORRECCIÓN: Usamos un selector de texto más específico para evitar la ambigüedad.**
        # Buscamos una parte del texto que sea única del cuerpo de la notificación.
        notification_text_locator = self.page.get_by_text("El evento 'Evento de Prueba Editado' ha tenido cambios")
        expect(notification_text_locator).to_be_visible()

