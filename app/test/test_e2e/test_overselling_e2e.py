import datetime
from django.utils import timezone
from playwright.sync_api import expect
from django.db import transaction
import time

from app.models import Event, User, Venue, Ticket
from app.test.test_e2e.base import BaseE2ETest


class OversellingPreventionTest(BaseE2ETest):
    """Tests relacionados con la prevención de overselling de tickets"""

    def setUp(self):
        super().setUp()

        # Usar el usuario organizador ya creado en BaseE2ETest
        self.organizer = User.objects.get(username="organizador")
        
        # Usar el usuario regular ya creado en BaseE2ETest
        self.regular_user = User.objects.get(username="usuario")
        
        # Crear un usuario adicional para tener más datos de prueba
        self.normie_user = self._create_test_user("normie", is_organizer=False)

        # Usar el venue ya creado en BaseE2ETest
        self.venue = Venue.objects.get(name="Venue de prueba")

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

    def _verify_ticket_creation(self, expected_count, expected_quantity=None):
        """Helper method para verificar la creación de tickets - optimizado para evitar repetición"""
        with transaction.atomic():
            self.assertEqual(Ticket.objects.count(), expected_count)
            if expected_quantity is not None:
                ticket = Ticket.objects.first()
                self.assertIsNotNone(ticket)
                if ticket is not None:
                    self.assertEqual(ticket.quantity, expected_quantity)
    
    def test_cannot_exceed_remaining_capacity(self):
        """Test que verifica que no se pueden comprar más tickets que los disponibles después de compras previas"""
        self.login_user("usuario", "password123")

        # Primera compra de tickets
        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/buy-ticket/")
        self.page.wait_for_selector("#quantity")
        self.page.fill("#quantity", "2")
        self.page.get_by_label("Tipo de entrada").select_option("GENERAL")
        self.complete_card_data_in_buy_ticket_form()
        self.page.get_by_role("button", name="Confirmar compra").click()
        self.page.wait_for_load_state("networkidle")
        
        # Verificar primera compra usando método helper (1 ticket VIP + 1 ticket GENERAL = 2 total)
        self._verify_ticket_creation(expected_count=2, expected_quantity=2)

        # Segunda compra de tickets (debería fallar o crear otro ticket)
        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/buy-ticket/")
        self.page.wait_for_selector("#quantity")
        self.page.fill("#quantity", "2")
        self.page.get_by_label("Tipo de entrada").select_option("GENERAL")
        self.complete_card_data_in_buy_ticket_form()
        self.page.get_by_role("button", name="Confirmar compra").click()

        # Verificar resultado final usando método helper (debería haber 1 VIP y 2 GENERAL = 3 tickets)
        self._verify_ticket_creation(expected_count=3, expected_quantity=2)