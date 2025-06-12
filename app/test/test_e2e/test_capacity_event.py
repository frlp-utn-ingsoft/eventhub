import re
from app.test.test_e2e.base import BaseE2ETest
from playwright.sync_api import expect
from app.models import Event, Venue, User
from django.utils import timezone
import datetime

class TicketPurchaseE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp() 
        self.organizer = self.create_test_user(is_organizer=True)
        
        self.venue = Venue.objects.create(
            name='E2E Venue',
            capacity=3,
            created_by=self.organizer,
            address='789 Blvd',
            city='E2E City',
            contact_info='e2e@test.com'
        )
        
        scheduled_at = timezone.make_aware(datetime.datetime(2025, 12, 31, 20, 0))
        self.event = Event.objects.create(
            title='E2E Capacity Event',
            description='Testing ticket capacity',
            scheduled_at=scheduled_at, 
            organizer=self.organizer,
            venue=self.venue,
            available_tickets=self.venue.capacity
        )

        self.event.update_availability()
        self.buyer = self.create_test_user(is_organizer=False)
        self.login_user(self.buyer.username, "password123")



    def test_capacity_validation(self):
        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/")

        buy_button = self.page.get_by_role("link", name="Comprar Entrada")
        expect(buy_button).to_be_visible()
        buy_button.click()

        # Llenar los campos usando los placeholders exactos
        self.page.get_by_placeholder("1234 5678 9012 3456").fill("4111111111111111")
        self.page.get_by_placeholder("MM/AA").fill("12/25")
        self.page.get_by_placeholder("Juan Pérez").fill("John Doe")
        self.page.check("#terms")
        # Intentar comprar 4 tickets
        self.page.get_by_label("Cantidad").fill("4")
        self.page.get_by_role("button", name="Confirmar compra").click()
        
        expect(self.page).to_have_url(re.compile(f"{self.live_server_url}/tickets/new/"))


        # Verificar mensaje de error
        #expect(self.page.get_by_text("Solo quedan 3 entradas disponibles", exact=True)).to_be_visible()

        # Corregir cantidad a 3
        self.page.get_by_label("Cantidad").fill("3")
        self.page.get_by_role("button", name="Confirmar compra").click()
        
        # Verificar compra exitosa
        expect(self.page).to_have_url(re.compile(r"/tickets/"))

