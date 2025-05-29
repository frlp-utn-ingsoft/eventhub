import datetime
import re
from django.utils import timezone
from playwright.sync_api import expect
from app.models import Event, User, Ticket, Venue
from app.test.test_e2e.base import BaseE2ETest


class TicketLimitE2ETest(BaseE2ETest):
    """Tests E2E para verificar el límite de tickets por usuario"""

    def setUp(self):
        super().setUp()

        # Crear usuario regular
        self.regular_user = User.objects.create_user(
            username="usuario",
            email="usuario@example.com",
            password="password123",
            is_organizer=False,
        )

        # Crear usuario regular
        self.other_user = User.objects.create_user(
            username="usuario2",
            email="usuario2@example.com",
            password="password123",
            is_organizer=False,
        )

        # Crear organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )

        # Crear evento
        event_date = timezone.now() + datetime.timedelta(days=5, hours=4, minutes=15)
        venue = Venue.objects.create(
            name="Auditorio Principal",
            address="Calle Falsa 123, Ciudad Ejemplo",
            capacity=3,
        )

        self.event = Event.objects.create(
            title="Concierto de prueba",
            description="Concierto limitado",
            scheduled_at=event_date,
            organizer=self.organizer,
        )

        self.event2 = Event.objects.create(
            title="Evento de prueba",
            description="Evento con capacidad 3",
            scheduled_at=event_date,
            organizer=self.organizer,
            venue=venue,
        )

    def llenar_formulario_pago(self):
        self.page.fill("#card_number", "1234567812345678")
        self.page.fill("#expiry_date", "2025-07")
        self.page.fill("#cvv", "123")
        self.page.fill("#card_name", "Usuario Ejemplo")
        self.page.check("#accept_terms")

    def comprar_ticket(self):
        self.page.goto(f"{self.live_server_url}/ticket/new/{self.event.id}/")
        self.llenar_formulario_pago()

        buy_button = self.page.get_by_role("button", name="Pagar y Comprar")
        expect(buy_button).to_be_visible()
        buy_button.click()

    def test_user_cannot_buy_more_than_4_tickets(self):
        """Verifica que un usuario no puede comprar más de 4 tickets para un mismo evento"""
        self.login_user("usuario", "password123")

        # Comprar los primeros 4 tickets
        for i in range(4):
            self.comprar_ticket()
        # Intentar comprar un 5º ticket
        self.comprar_ticket()
        # Verificar en la base de datos
        ticket_count = Ticket.objects.filter(user=self.regular_user, event=self.event).count()
        self.assertEqual(ticket_count, 4)

    def test_alert_visibility_on_soldout(self):
        """Verifica que la alerta de sold out se muestra correctamente en caso de intentar comprar un evento con tickets agotados"""

        self.login_user("usuario2", "password123")

        # Compra los 3 tickets disponibles
        for i in range(3):
            self.page.goto(f"{self.live_server_url}/ticket/new/{self.event2.id}/")
            alert = self.page.locator("#alert-error")
            # La alerta deberia ser invisible
            expect(alert).to_be_visible(visible=False)
            self.llenar_formulario_pago()
            buy_button = self.page.get_by_role("button", name="Pagar y Comprar")
            expect(buy_button).to_be_visible()
            buy_button.click()

        # Logout
        self.page.goto(f"{self.live_server_url}/events/")
        self.page.get_by_role("button", name="Salir").click()

        # Login otro usuario
        self.login_user("usuario", "password123")

        # Intentar comprar un ticket adicional
        self.page.goto(f"{self.live_server_url}/ticket/new/{self.event2.id}/")
        alert = self.page.locator("#alert-error")
        expect(alert).to_be_visible()
