from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
import datetime
from decimal import Decimal

from app.models import Event, User, Location, Ticket

class EventDemandIntegrationTest(TestCase):
    def setUp(self):
        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )

        # Crear usuario regular
        self.regular_user = User.objects.create_user(
            username="regular",
            email="regular@test.com",
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
            price_general=Decimal('100.00'),
            price_vip=Decimal('200.00')
        )

        # Cliente para hacer peticiones
        self.client = Client()

    def test_basic_info(self):
        """Test que verifica que la vista de detalle muestra la información básica del evento"""
        # Login como usuario regular
        self.client.login(username="regular", password="password123")

        # Hacer petición a la vista de detalle
        response = self.client.get(reverse("event_detail", args=[self.event.id]))

        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/event_detail.html")
        # No debe mostrar tickets vendidos ni estado de demanda
        self.assertNotContains(response, "Tickets vendidos")
        self.assertNotContains(response, "Estado de demanda")

    def test_organizer_can_see_demand_info(self):
        """Test que verifica que el organizador puede ver la información de demanda"""
        # Login como organizador
        self.client.login(username="organizador", password="password123")

        # Vender entradas para el evento
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

        # Hacer petición a la vista de detalle
        response = self.client.get(reverse("event_detail", args=[self.event.id]))

        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        # Debe mostrar tickets vendidos y estado de demanda
        self.assertContains(response, "Tickets vendidos")
        self.assertContains(response, str(self.event.tickets_sold))
        self.assertContains(response, "Estado de demanda")
        self.assertContains(response, self.event.demand_status)

    def test_regular_user_cannot_see_demand_info(self):
        """Test que verifica que un usuario regular no puede ver la información de demanda"""
        # Login como usuario regular
        self.client.login(username="regular", password="password123")

        # Vender entradas para el evento
        Ticket.objects.create(
            event=self.event,
            type='general',
            quantity=1,
            card_type='credit',
            user=self.regular_user
        )

        # Actualizar el contador de entradas vendidas
        self.event.tickets_sold = Ticket.objects.filter(event=self.event).count()
        self.event.save()

        # Hacer petición a la vista de detalle
        response = self.client.get(reverse("event_detail", args=[self.event.id]))

        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        # No debe mostrar tickets vendidos ni estado de demanda
        self.assertNotContains(response, "Tickets vendidos")
        self.assertNotContains(response, "Estado de demanda")

    def test_demand_info_updates_after_ticket_purchase(self):
        """Test que verifica que la información de demanda se actualiza después de comprar entradas"""
        # Login como organizador
        self.client.login(username="organizador", password="password123")

        # Verificar estado inicial
        response = self.client.get(reverse("event_detail", args=[self.event.id]))
        self.assertContains(response, "Tickets vendidos")
        self.assertContains(response, "0")
        self.assertContains(response, "Estado de demanda")
        self.assertContains(response, self.event.demand_status)

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

        # Verificar estado actualizado
        response = self.client.get(reverse("event_detail", args=[self.event.id]))
        self.assertContains(response, "Tickets vendidos")
        self.assertContains(response, str(self.event.tickets_sold))
        self.assertContains(response, "Estado de demanda")
        self.assertContains(response, self.event.demand_status)

    def test_organizer_can_see_demand_info_with_multiple_tickets(self):
        """Test que verifica que el organizador puede ver la información de demanda con múltiples entradas"""
        # Login como organizador
        self.client.login(username="organizador", password="password123")

        # Vender entradas para el evento
        for _ in range(10):
            Ticket.objects.create(
                event=self.event,
                type='vip',
                quantity=1,
                card_type='debit',
                user=self.organizer
            )

        # Actualizar el contador de entradas vendidas
        self.event.tickets_sold = Ticket.objects.filter(event=self.event).count()
        self.event.save()

        # Hacer petición a la vista de detalle
        response = self.client.get(reverse("event_detail", args=[self.event.id]))

        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tickets vendidos")
        self.assertContains(response, str(self.event.tickets_sold))
        self.assertContains(response, "Estado de demanda")
        self.assertContains(response, self.event.demand_status)

    def test_regular_user_cannot_see_demand_info_with_multiple_tickets(self):
        """Test que verifica que un usuario regular no puede ver la información de demanda con múltiples entradas"""
        # Login como usuario regular
        self.client.login(username="regular", password="password123")

        # Vender entradas para el evento
        for _ in range(10):
            Ticket.objects.create(
                event=self.event,
                type='vip',
                quantity=1,
                card_type='debit',
                user=self.regular_user
            )

        # Actualizar el contador de entradas vendidas
        self.event.tickets_sold = Ticket.objects.filter(event=self.event).count()
        self.event.save()

        # Hacer petición a la vista de detalle
        response = self.client.get(reverse("event_detail", args=[self.event.id]))

        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Tickets vendidos")
        self.assertNotContains(response, "Estado de demanda") 