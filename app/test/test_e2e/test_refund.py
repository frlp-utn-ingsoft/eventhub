import datetime
from django.utils import timezone
from playwright.sync_api import expect
from app.models import User, Event, Ticket, Refund
from app.test.test_e2e.base import BaseE2ETest

class RefundE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()
        # crear user y event
        self.user = User.objects.create_user(
            username="e2euser", email="user@example.com", password="pass123"
        )
        self.organizer = User.objects.create_user(
            username="e2eorg", email="org@example.com", password="pass123", is_organizer=True
        )
        event_date = timezone.now() + timezone.timedelta(days=1)
        self.event = Event.objects.create(
            title="E1", description="Desc", scheduled_at=event_date, organizer=self.organizer
        )
        self.ticket = Ticket.objects.create(
            user=self.user, event=self.event, quantity=1, type="GENERAL"
        )

    def test_request_refund_flow(self):
        # login
        self.login_user('e2euser','pass123')
        # ir a mis reembolsos y no hay
        self.page.goto(f"{self.live_server_url}/refunds/")
        expect(self.page.locator('text=No hiciste ninguna')).to_be_visible()
        # crear refund
        self.page.goto(f"{self.live_server_url}/refunds/new/")
        self.page.select_option('#ticket_code', self.ticket.ticket_code)
        self.page.fill('#reason','motivo')
        self.page.click('button:has-text("Guardar")')
        # verificar redirect y existencia
        expect(self.page).to_have_url(f"{self.live_server_url}/refunds/")
        assert Refund.objects.filter(user=self.user, ticket_code=self.ticket.ticket_code).exists()
        # intentar duplicar
        self.page.goto(f"{self.live_server_url}/refunds/new/")
        self.page.select_option('#ticket_code', self.ticket.ticket_code)
        self.page.fill('#reason','motivo')
        self.page.click('button:has-text("Guardar")')
        expect(self.page.locator('.alert-danger')).to_be_visible()