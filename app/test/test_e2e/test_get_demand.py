from playwright.sync_api import expect
from app.models import Ticket, User, Venue,Category, Event  
from app.test.test_e2e.base import BaseE2ETest
import datetime
from django.utils import timezone

class EventDetailGetDemandE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()
        self.organizer = User.objects.create_user(
            username="Organizador",
            password="password123",
            is_organizer=True,
        )
        self.venue = Venue.objects.create(
            name="Auditorio Principal",
            adress="Calle Falsa 123",
            city="Ciudad Autonoma de Buenos Aires",
            capacity=2,
            contact="Juan Perez",
        )
        self.category = Category.objects.create(
            name="Rock",
            is_active=True,
            description="Rock y sus derivados",
        )
        event_date = timezone.make_aware(datetime.datetime(2025, 2, 10, 10, 10))
        self.event = Event.objects.create(
            title="Evento de prueba 1",
            description="Descripción del evento 1",
            scheduled_at=event_date,
            venue=self.venue,
            organizer=self.organizer,
            category=self.category,
        )
        self.user1 = User.objects.create_user(
            username="usuario1",
            password="password123",
            is_organizer=False,
        )
        self.user2 = User.objects.create_user(
            username="usuario2",
            password="password123",
            is_organizer=False,
        )

    def test_event_get_demand(self):
        """Test que verifica la demanda y la cantidad de entradas vendidas en el detalle del evento"""
        # Login como organizador
        self.page.goto(f"{self.live_server_url}/accounts/login/")
        self.page.fill('input[name="username"]', "Organizador")
        self.page.fill('input[name="password"]', "password123")             
        self.page.click('button[type="submit"]')

        # Ir al detalle del evento (sin tickets, debe ser baja demanda)
        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/")
        expect(self.page.locator("text=Baja demanda")).to_be_visible()

        # Creamos tickets para el evento
        Ticket.objects.create(
                user=self.user1,
                event=self.event,
                type="general",
                quantity=1
            )
        Ticket.objects.create(
                user=self.user2,
                event=self.event,
                type="general",
                quantity=1
            )
   
        # Refrescar la página de detalle
        self.page.reload()
        expect(self.page.locator("text=Alta demanda")).to_be_visible()
