import datetime
from django.utils import timezone
from decimal import Decimal
from playwright.sync_api import expect

from app.models import Event, User, Location, Ticket
from app.test.test_e2e.base import BaseE2ETest

class TicketsLimitE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()

        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )

        # Crear usuario comprador
        self.comprador = User.objects.create_user(
            username="comprador",
            email="comprador@test.com",
            password="password123",
            is_organizer=False,
        )

        # Crear ubicación
        self.location = Location.objects.create(
            name="Sala Principal",
            address="Calle Principal 123",
            city="Ciudad",
            capacity=100
        )

        # Crear evento con límite de tickets
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            location=self.location,
            tickets_total=3,
            price_general=Decimal('100.00'),
            price_vip=Decimal('200.00')
        )

    def test_tickets_limit(self):
        """Test que verifica que no se pueden comprar más tickets que los disponibles"""
        # Simular la venta de todas las entradas disponibles
        for _ in range(self.event.tickets_total):
            Ticket.objects.create(
                event=self.event,
                type='general',
                quantity=1,
                card_type='credit',
                user=self.comprador
            )

        # Login como comprador e intentar comprar un ticket más vía interfaz
        self.login_user("comprador", "password123")
        url = f"{self.live_server_url}/tickets/buy/{self.event.id}/"
        self.page.goto(url)
        
        # Esperar a que los elementos estén disponibles y llenar el formulario
        self.page.wait_for_selector('#id_type')
        self.page.select_option('#id_type', 'general')
        self.page.wait_for_selector('#id_quantity')
        self.page.fill('#id_quantity', '1')
        self.page.wait_for_selector('#id_card_type')
        self.page.select_option('#id_card_type', 'credit')
        self.page.wait_for_selector('#id_card_number')
        self.page.fill('#id_card_number', '1234567812345678')
        self.page.wait_for_selector('#id_expiry_month')
        self.page.select_option('#id_expiry_month', '12')
        expiry_year = self.page.locator("#id_expiry_year option").nth(1).get_attribute("value")
        self.page.select_option('#id_expiry_year', expiry_year)
        self.page.wait_for_selector('#id_card_cvv')
        self.page.fill('#id_card_cvv', '123')
        self.page.get_by_label("Acepto los términos y condiciones y la política de privacidad.").check()
        self.page.get_by_role("button", name="Confirmar compra").click()

        # Validar mensaje de error por límite de tickets
        expect(self.page.locator("text=No hay entradas disponibles")).to_be_visible()