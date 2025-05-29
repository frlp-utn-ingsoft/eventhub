from playwright.sync_api import expect
from app.models import Ticket, User
from app.test.test_e2e.base import BaseE2ETest

class EventDetailGetDemandE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()
        # Eliminar usuario si ya existe
        User.objects.filter(username="organizador").delete()
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )
        # Crea venue y evento como en tu setUp original
        from app.models import Venue, Category, Event
        self.venue1 = Venue.objects.create(
            name="Auditorio Principal",
            adress="Calle Falsa 123",
            city="Ciudad Autonoma de Buenos Aires",
            capacity=100,
            contact="Juan Perez",
        )
        self.category = Category.objects.create(
            name="Rock",
            is_active=True,
            description="Rock y sus derivados",
        )
        import datetime
        from django.utils import timezone
        event_date1 = timezone.make_aware(datetime.datetime(2025, 2, 10, 10, 10))
        self.event1 = Event.objects.create(
            title="Evento de prueba 1",
            description="Descripción del evento 1",
            scheduled_at=event_date1,
            venue=self.venue1,
            organizer=self.organizer,
            category=self.category,
        )

    def test_event_get_demand(self):
        """Test que verifica la demanda y la cantidad de entradas vendidas en el detalle del evento"""
        # Login como organizador
        self.page.goto(f"{self.live_server_url}/accounts/login/")
        self.page.fill('input[name="username"]', "organizador")
        self.page.fill('input[name="password"]', "password123")             
        self.page.click('button[type="submit"]')

        # Ir al detalle del evento (sin tickets, debe ser baja demanda)
        self.page.goto(f"{self.live_server_url}/events/{self.event1.id}/")
        expect(self.page.locator("text=Baja demanda")).to_be_visible()

        # Crear 91 tickets para superar el 90% de ocupación (capacidad 100)
        for i in range(91):
            user = User.objects.create_user(
                username=f"e2e_user_{i}",
                email=f"e2e_user_{i}@test.com",
                password="password123"
            )
            Ticket.objects.create(
                user=user,
                event=self.event1,
                type="general",
                quantity=1
            )

        # Refrescar la página de detalle
        self.page.reload()
        expect(self.page.locator("text=Alta demanda")).to_be_visible()
        expect(self.page.locator("text=91")).to_be_visible()  # Entradas vendidas: 91