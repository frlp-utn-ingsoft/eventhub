import datetime

from django.utils import timezone
from playwright.sync_api import expect

from app.models import Event, User
from tickets.models import Ticket

from .base import BaseE2ETest


class TicketCreationE2ETest(BaseE2ETest):
    """Test E2E para validación de límite de 4 entradas por evento por usuario"""

    def setUp(self):
        super().setUp()

        self.organizer = User.objects.create_user(
            username="usuario_test2",
            email="test2@example.com",
            password="password123",
            is_organizer=True,
        )
        self.user = self.create_test_user()
        

        event_date = timezone.localtime() - datetime.timedelta(days=60)
        self.event = Event.objects.create(
            title="Evento de prueba 1",
            description="Descripción del evento 1",
            scheduled_at=event_date,
            organizer=self.organizer,
        )

    def test_user_cannot_exceed_4_tickets_limit(self):
        """Test: No se puede exceder el límite de 4 entradas"""
        
        self.login_user("usuario_test", "password123")
        

        self.page.goto(f"{self.live_server_url}/tickets/{self.event.id}/")# type:ignore
        self.page.get_by_label("Cantidad de entradas").fill("5")
        

        self.page.fill("#card-number", "1234 5678 9012 3456")
        self.page.fill("#expiry-date", "2025-12")
        self.page.fill("#cvv", "123")
        self.page.fill("#card-name", "Juan Pérez")
        self.page.check("#terms")
        
        self.page.click("button:has-text('Confirmar compra')")
        

        expect(self.page.locator("#quantity:invalid")).to_be_visible()

        total_entries = sum(
            ticket.quantity for ticket in 
            Ticket.objects.filter(user=self.user, event=self.event)
        )
        self.assertEqual(total_entries, 0)

    def test_user_can_buy_exactly_4_tickets(self):
        """Test: Usuario puede comprar exactamente 4 entradas de una vez"""
        
        self.login_user("usuario_test", "password123")
        

        self.page.goto(f"{self.live_server_url}/tickets/{self.event.id}/")# type:ignore
        self.page.get_by_label("Cantidad de entradas").fill("4")
        

        self.page.fill("#card-number", "1234 5678 9012 3456")
        self.page.fill("#expiry-date", "2025-12")
        self.page.fill("#cvv", "123")
        self.page.fill("#card-name", "Juan Pérez")
        self.page.check("#terms")
        
        self.page.click("button:has-text('Confirmar compra')")
        

        expect(self.page).to_have_url(f"{self.live_server_url}/events/")# type:ignore
        

        total_entries = sum(
            ticket.quantity for ticket in 
            Ticket.objects.filter(user=self.user, event=self.event)
        )
        self.assertEqual(total_entries, 4)