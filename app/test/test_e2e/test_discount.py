import datetime

from django.utils import timezone
from playwright.sync_api import expect

from app.models import Event, User, Discount, Venue

from app.test.test_e2e.base import BaseE2ETest


class DiscountBaseTest(BaseE2ETest):
    """
    Clase base con la configuración común para todos los test de descuentos.
    """

    def setUp(self):
        super().setUp()
        # Crear un usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )

        # Crear un usuario regular
        self.regular_user = User.objects.create_user(
            username="regular",
            email="regular@test.com",
            password="password123",
            is_organizer=False,
        )

        # Crear una localización de prueba
        self.venue = Venue.objects.create(
            name = "venue__name-test",
            adress = "venue__adress-test",
            city = "venue__city-test",
            capacity = 15000,
            contact = "venue__contac-test"
        )

        # Crear algunos eventos de prueba
        self.event1 = Event.objects.create(
            title="Evento 1",
            description="Descripción del evento 1",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue= self.venue
        )
        
        self.discount = Discount.objects.create (
            code="UTN-FRLP",
            multiplier=0.8
        )

class DiscountBuyingTicketTest(DiscountBaseTest):
    """
    Tests que verifica si se aplica el descuento al comprar un  
    """
    def test_validate_discount(self):
        """
        Verifica que el código enviado sea válido.
        """
        # Login con usuario regular
        self.login_user("regular", "password123")
        
        self.page.goto(f"{self.live_server_url}/events/{self.event1.id}/buy-ticket/")

        self.page.wait_for_load_state("networkidle")

        discount_toggle = self.page.locator("#discount-toggle")
        expect(discount_toggle).to_be_visible(timeout=5000)

        discount_toggle.click()

        self.page.wait_for_selector("#discount-code", state="visible")

        discount_code_input = self.page.get_by_label("Código de descuento")
        expect(discount_code_input).to_be_visible(timeout=5000)

        discount_code_input.fill('UTN-FRLP')

        verify_discount_button = self.page.locator('#verify-discount')
        
        expect(verify_discount_button).to_be_attached(timeout=5000)
        verify_discount_button.click()

        self.page.wait_for_selector("#discount-message", state="visible")
        
        discount_message = self.page.locator('#discount-message')
        expect(discount_message).to_have_text("Código validado correctamente")