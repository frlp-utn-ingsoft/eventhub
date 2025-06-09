import datetime
from django.utils import timezone
from playwright.sync_api import expect
from django.db import transaction
from typing import cast
import time

from app.models import Event, User, Venue, Ticket
from app.test.test_e2e.base import BaseE2ETest


class OversellingPreventionTest(BaseE2ETest):
    """Tests relacionados con la prevención de overselling de tickets"""

    def setUp(self):
        super().setUp()

        sufijo = str(int(time.time() * 1000))
        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username=f"organizador_{sufijo}",
            email=f"organizador_{sufijo}@example.com",
            password="password123",
            is_organizer=True,
        )

        # Crear usuario regular
        self.regular_user = User.objects.create_user(
            username=f"usuario_{sufijo}",
            email=f"usuario_{sufijo}@example.com",
            password="password123",
            is_organizer=False,
        )

        self.normie_user = User.objects.create_user(
            username="normie",
            email=f"usuario_normie@example.com",
            password="password123",
            is_organizer=False,
        )

        # Crear venue con capacidad limitada
        self.venue = Venue.objects.create(
            name="Venue de prueba",
            adress="Dirección de prueba",
            city="Ciudad de prueba",
            capacity=4,  # Capacidad pequeña para facilitar las pruebas
            contact="contacto@test.com"
        )

        # Crear evento de prueba
        event_date = timezone.make_aware(datetime.datetime(2030, 2, 10, 10, 10))
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento",
            scheduled_at=event_date,
            organizer=self.organizer,
            venue=self.venue
        )

        self.ticket = Ticket.objects.create(
            quantity=1,
            type="VIP",
            event=self.event,
            user=self.normie_user
        )

    def _create_test_user(self, username_suffix, is_organizer=False):
        """Helper method para crear usuarios de prueba - optimizado para evitar repetición"""
        return User.objects.create_user(
            username=f"testuser_{username_suffix}",
            email=f"testuser_{username_suffix}@example.com",
            password="password123",
            is_organizer=is_organizer,
        )
    
    def test_cannot_exceed_remaining_capacity(self):
        """Test que verifica que no se pueden comprar más tickets que los disponibles después de compras previas"""
        self.login_user("usuario", "password123")
        event_id = cast(int, self.event.id)  # type: ignore

        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/buy-ticket/")
        self.page.wait_for_selector("#quantity")
        self.page.fill("#quantity", "2")
        self.page.get_by_label("Tipo de entrada").select_option("GENERAL")
        self.complete_card_data_in_buy_ticket_form()
        self.page.get_by_role("button", name="Confirmar compra").click()
        self.page.wait_for_load_state("networkidle")
        with transaction.atomic():
            ticket = cast(Ticket, Ticket.objects.first())  # type: ignore
            self.assertIsNotNone(ticket)
            self.assertEqual(ticket.quantity, 2)

        # Navegar nuevamente a la página de compra
        self.page.goto(f"{self.live_server_url}/events/{event_id}/buy-ticket/")
        self.page.wait_for_selector("#quantity")
        self.page.fill("#quantity", "2")
        self.page.get_by_label("Tipo de entrada").select_option("GENERAL")
        self.complete_card_data_in_buy_ticket_form()
        self.page.get_by_role("button", name="Confirmar compra").click()

#        error_message = self.page.get_by_text("No hay suficientes entradas disponibles. Solo quedan 2 entradas.")
#        expect(error_message).to_be_visible()

        with transaction.atomic():
            self.assertEqual(Ticket.objects.count(), 2)
            ticket = cast(Ticket, Ticket.objects.first())  # type: ignore
            self.assertIsNotNone(ticket)
            self.assertEqual(ticket.quantity, 2)