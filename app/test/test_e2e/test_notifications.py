from django.utils import timezone
from app.models import Event, Venue, User, Notification, Category, Ticket
import datetime
from app.test.test_e2e.base import BaseE2ETest
from playwright.sync_api import expect

class NotificationE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()
        
        # Crear usuario organizador con nombre único
        self.organizer = User.objects.create_user(
            username="Organizer",
            password="password123",
            is_organizer=True,
        )

        # Crear usuario regular con nombre único
        self.regular_user = User.objects.create_user(
            username="Normie",
            password="password123",
            is_organizer=False,
        )

        # Crear venues
        self.venue1 = Venue.objects.create(
            name="Lugar 1",
            adress="Dirección 1",
            city="Ciudad 1",
            capacity=100,
            contact="Contacto 1"
        )
        self.venue2 = Venue.objects.create(
            name="Lugar 2",
            adress="Dirección 2",
            city="Ciudad 2",
            capacity=200,
            contact="Contacto 2"
        )

        # Crear categoría
        self.category = Category.objects.create(
            name="Categoría de prueba",
            description="Descripción de prueba",
            is_active=True
        )

        # Crear evento con fecha y hora fijas
        tomorrow = timezone.now() + datetime.timedelta(days=1)
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.make_aware(
                datetime.datetime.combine(
                    tomorrow.date(),
                    datetime.time(hour=15, minute=30)
                )
            ),
            organizer=self.organizer,
            venue=self.venue1,
            category=self.category,
        )

        # Crear tickets para el usuario regular
        Ticket.objects.create(
            event=self.event,
            user=self.regular_user,
            quantity=1,
            type="GENERAL"
        )

    def test_notification_created_on_event_update(self):
        """Test end-to-end que verifica el flujo completo de actualización de evento y notificación"""
        # Iniciar sesión como organizador
        self.login_user(self.organizer.username, "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        # Hacer clic en el botón editar del evento
        self.page.get_by_role("link", name="Editar").first.click()

        # Verificar que estamos en la página de edición
        expect(self.page).to_have_url(f"{self.live_server_url}/events/{self.event.id}/edit/")

        # Editar fecha y lugar
        date = self.page.get_by_label("Fecha")
        expect(date).to_have_value(self.event.scheduled_at.strftime("%Y-%m-%d"))
        date.fill("2025-04-20")

        time = self.page.get_by_label("Hora")
        expect(time).to_have_value("15:30")
        time.fill("15:30")

        venue = self.page.get_by_label("Lugar")
        expect(venue).to_have_value(str(self.venue1.id))
        venue.select_option(value=str(self.venue2.id))

        # Guardar cambios
        self.page.get_by_role("button", name="Guardar Cambios").click()

        # Verificar que redirigió a la página de eventos
        expect(self.page).to_have_url(f"{self.live_server_url}/events/")

        # Cerrar sesión como organizador
        self.page.get_by_role("button", name="Salir").click()

        # Iniciar sesión como usuario regular
        self.login_user(self.regular_user.username, "password123")

        # Ir a la página de notificaciones
        self.page.goto(f"{self.live_server_url}/notifications/")

        # Verificar que existe la notificación en el perfil del usuario
        notification = self.page.get_by_text("Evento actualizado")
        expect(notification).to_be_visible()
