from .base import BaseE2ETest
from playwright.sync_api import expect
from app.models import Venue, Event, Ticket, User
from datetime import datetime
from django.utils import timezone
from django.utils.timezone import now, timedelta
import re

class TicketE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()

        self.user = self.create_test_user()

        self.organizer = User.objects.create_user(
            username="organizer_test",
            email="organizer_test@example.com",
            password="password123",
            is_organizer=True
        )

        self.venue1 = Venue.objects.create(
            name="Estadio A",
            address="Calle A",
            city="Ciudad",
            capacity=1000,
            contact="mail@test.com"
        )
        self.venue2 = Venue.objects.create(
            name="Estadio B",
            address="Calle B",
            city="Ciudad",
            capacity=8000,
            contact="mail2@test.com"
        )

        self.event = Event.objects.create(
            title="Evento E2E",
            description="Descripción",
            scheduled_at=now() + timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue1
        )

        Ticket.objects.create(
            event=self.event,
            user=self.user,
            quantity=2,
            type="GENERAL"
        )

        self.user2 = User.objects.create_user(
            username="segundo_usuario",
            email="segundo@example.com",
            password="password456"
        )

        Ticket.objects.create(
            event=self.event,
            user=self.user2,
            quantity=1,
            type="GENERAL"
        )


    def test_successful_ticket_purchase_flow(self):
        self.login_user("usuario_test", "password123")
        self.page.goto(f"{self.live_server_url}/events")

        # Ver el evento y clickear en "Comprar Ticket"
        expect(self.page.locator(f"text={self.event.title}")).to_be_visible()
        self.page.click(f"text={self.event.title}")
        self.page.click("a[aria-label='Comprar Ticket']")
        expect(self.page.locator("div.card-body form")).to_be_visible()

        expect(self.page.locator('input[name="card_name"]')).to_be_visible()
        expect(self.page.locator('input[name="card_number"]')).to_be_visible()
        expect(self.page.locator('input[name="expiration_date"]')).to_be_visible()
        expect(self.page.locator('input[name="cvv"]')).to_be_visible()
        expect(self.page.locator('input[name="quantity"]')).to_be_visible()
        expect(self.page.locator('select[name="type"]')).to_be_visible()
        expect(self.page.locator('input[name="accept_terms"]')).to_be_visible()

        # Completar el formulario de compra
        self.page.fill('input[name="card_name"]', "Test User")
        self.page.fill('input[name="card_number"]', "1234567890123456")
        self.page.fill('input[name="expiration_date"]', "12/26")
        self.page.fill('input[name="cvv"]', "123")
        self.page.fill('input[name="quantity"]', "1")
        self.page.select_option('select[name="type"]', "GENERAL")
        self.page.check('input[name="accept_terms"]')
        self.page.get_by_role("button", name="Confirmar Compra").click()
        

        # Redirección a encuesta
        expect(self.page).to_have_url(re.compile(f"{self.live_server_url}/encuesta/\\d+/"))

        # Verificar que la encuesta está visible
        expect(self.page.locator('div.star-rating')).to_be_visible()
        expect(self.page.locator('textarea[name="issue"]')).to_be_visible()
        expect(self.page.locator('input[name="recommend"][value="True"]')).to_be_visible()
        expect(self.page.locator('input[name="recommend"][value="False"]')).to_be_visible()

        expect(self.page.locator('div.star-rating[data-input-id="star-input-satisfaction"] i.star[data-value="5"]')).to_be_visible()
        self.page.click('div.star-rating[data-input-id="star-input-satisfaction"] i.star[data-value="5"]')
        self.page.fill('textarea[name="issue"]', "Todo excelente.")
        self.page.check('input[name="recommend"][value="True"]')
        self.page.click("text=Enviar Encuesta")

        # Redirección a lista de tickets
        expect(self.page).to_have_url(f"{self.live_server_url}/tickets/")
        expect(self.page.locator("table")).to_be_visible()
        expect(self.page.locator("table")).to_contain_text(self.event.title)


    def test_ticket_purchase_with_invalid_card_fails(self):
        self.login_user("usuario_test", "password123")
        self.page.goto(f"{self.live_server_url}/events")
        self.page.click(f"text={self.event.title}")
        self.page.click("text=Comprar Ticket")
        expect(self.page.locator("div.card-body form")).to_be_visible()

        expect(self.page.locator('input[name="card_name"]')).to_be_visible()
        expect(self.page.locator('input[name="card_number"]')).to_be_visible()
        expect(self.page.locator('input[name="expiration_date"]')).to_be_visible()
        expect(self.page.locator('input[name="cvv"]')).to_be_visible()
        expect(self.page.locator('input[name="quantity"]')).to_be_visible()
        expect(self.page.locator('select[name="type"]')).to_be_visible()
        expect(self.page.locator('input[name="accept_terms"]')).to_be_visible()

        # Formulario con datos inválidos
        self.page.fill('input[name="card_name"]', "Test User")
        self.page.fill('input[name="card_number"]', "123")
        self.page.fill('input[name="expiration_date"]', "12/26")
        self.page.fill('input[name="cvv"]', "123")
        self.page.fill('input[name="quantity"]', "1")
        self.page.select_option('select[name="type"]', "GENERAL")
        self.page.check('input[name="accept_terms"]')
        self.page.click("text=Confirmar Compra")

        # Verificar que sigamos en la misma página y aparezca error
        expect(self.page.locator("body")).to_contain_text("corrige los siguientes errores")
        expect(self.page.locator("#id_card_number_error")).to_contain_text(
            "Asegúrese de que este valor tenga como mínimo 13 caracteres"
        )
