import datetime
from django.utils import timezone
from decimal import Decimal
from playwright.sync_api import expect

from app.models import Event, User, Location, Ticket
from app.test.test_e2e.base import BaseE2ETest

class EventDemandE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()

        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )

        # Crear usuario regular
        self.regular_user = User.objects.create_user(
            username="usuario",
            email="usuario@example.com",
            password="password123",
            is_organizer=False,
        )

        # Crear ubicación con capacidad
        self.location = Location.objects.create(
            name="Sala Principal",
            address="Calle Principal 123",
            city="Ciudad",
            capacity=100
        )

        # Crear evento
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            location=self.location,
            tickets_total=int("100"),
            price_general=Decimal('100.00'),
            price_vip=Decimal('200.00')
        )

    def test_organizer_can_see_demand_info(self):
        """Test que verifica que el organizador puede ver la información de demanda en la interfaz"""
        # Login como organizador
        self.login_user("organizador", "password123")

        # Ir a la página de detalle del evento
        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/")

        # Verificar que se muestra la información de demanda
        demand_info = self.page.locator('.demand-info')
        tickets_sold_info = self.page.locator('.ticket-info:has-text("Tickets vendidos")')
        tickets_available_info = self.page.locator('.ticket-info:has-text("Tickets disponibles")')
        
        expect(demand_info).to_contain_text('Estado de demanda')
        expect(demand_info).to_contain_text('Baja demanda')
        expect(tickets_sold_info).to_contain_text('Tickets vendidos')
        expect(tickets_sold_info).to_contain_text('0')
        expect(tickets_available_info).to_contain_text('Tickets disponibles')

        # Vender algunas entradas
        for _ in range(90):
            Ticket.objects.create(
                event=self.event,
                type='general',
                quantity=1,
                card_type='credit',
                user=self.organizer
            )

        # Actualizar el contador de entradas vendidas
        self.event.tickets_sold = Ticket.objects.filter(event=self.event).count()
        self.event.save()

        # Recargar la página
        self.page.reload()

        # Verificar que la información se actualizó
        expect(demand_info).to_contain_text('Estado de demanda')
        expect(demand_info).to_contain_text('Alta demanda')
        expect(tickets_sold_info).to_contain_text('Tickets vendidos')
        expect(tickets_sold_info).to_contain_text('90')

    def test_regular_user_cannot_see_demand_info(self):
        """Test que verifica que un usuario regular no puede ver la información de demanda"""
        # Login como usuario regular
        self.login_user("usuario", "password123")

        # Ir a la página de detalle del evento
        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/")

        # Verificar que NO se muestra la información de demanda
        expect(self.page.locator('.demand-info')).not_to_be_visible()
        expect(self.page.locator('.ticket-info')).not_to_be_visible()

    def test_demand_info_updates_after_ticket_purchase(self):
        """Test que verifica que la información de demanda se actualiza después de comprar entradas"""
        # Login como organizador
        self.login_user("organizador", "password123")

        # Ir a la página de detalle del evento
        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/")

        # Verificar estado inicial
        demand_info = self.page.locator('.demand-info')
        tickets_sold_info = self.page.locator('.ticket-info:has-text("Tickets vendidos")')
        tickets_available_info = self.page.locator('.ticket-info:has-text("Tickets disponibles")')
        
        expect(demand_info).to_contain_text('Estado de demanda')
        expect(demand_info).to_contain_text('Baja demanda')
        expect(tickets_sold_info).to_contain_text('Tickets vendidos')
        expect(tickets_sold_info).to_contain_text('0')
        expect(tickets_available_info).to_contain_text('Tickets disponibles')

        # Simular compra de entradas
        for _ in range(25):
            Ticket.objects.create(
                event=self.event,
                type='general',
                quantity=1,
                card_type='credit',
                user=self.organizer
            )

        # Actualizar el contador de entradas vendidas
        self.event.tickets_sold = Ticket.objects.filter(event=self.event).count()
        self.event.save()

        # Recargar la página
        self.page.reload()

        # Verificar que la información se actualizó
        expect(demand_info).to_contain_text('Estado de demanda')
        expect(demand_info).to_contain_text('Demanda normal')
        expect(tickets_sold_info).to_contain_text('Tickets vendidos')
        expect(tickets_sold_info).to_contain_text('25') 