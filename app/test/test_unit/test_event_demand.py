from django.test import TestCase
from django.utils import timezone
import datetime
from decimal import Decimal

from app.models import Event, User, Location, Ticket

class EventDemandTest(TestCase):
    def setUp(self):
        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
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

    def test_tickets_left_calculation(self):
        """Test que verifica el cálculo correcto de entradas restantes"""
        # Verificar que inicialmente hay 100 entradas disponibles
        self.assertEqual(self.event.tickets_available, 100)

        # Vender algunas entradas
        Ticket.objects.create(
            event=self.event,
            type='general',
            quantity=1,
            card_type='credit',
            user=self.organizer
        )
        Ticket.objects.create(
            event=self.event,
            type='vip',
            quantity=1,
            card_type='credit',
            user=self.organizer
        )

        # Actualizar el contador de entradas vendidas
        self.event.tickets_sold = Ticket.objects.filter(event=self.event).count()
        self.event.save()

        # Verificar que quedan 98 entradas
        self.assertEqual(self.event.tickets_available, 98)

    def test_occupancy_percentage_calculation(self):
        """Test que verifica el cálculo correcto del porcentaje de ocupación"""
        # Verificar que inicialmente la ocupación es 0%
        self.assertEqual(self.event.occupancy_percentage, 0.0)

        # Vender 50 entradas
        for _ in range(50):
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

        # Verificar que la ocupación es 50%
        self.assertEqual(self.event.occupancy_percentage, 50.0)

    def test_demand_status_calculation(self):
        """Test que verifica el cálculo correcto del estado de demanda"""
        # Verificar que inicialmente la demanda es baja
        self.assertEqual(self.event.demand_status, "Baja demanda")

        # Vender 90 entradas (90% de ocupación)
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

        # Verificar que la demanda es alta
        self.assertEqual(self.event.demand_status, "Alta demanda")

        # Vender solo 5 entradas (5% de ocupación)
        self.event.tickets_sold = 5
        self.event.save()

        # Verificar que la demanda es baja
        self.assertEqual(self.event.demand_status, "Baja demanda")

    def test_event_without_location(self):
        """Test que verifica el comportamiento cuando el evento no tiene ubicación"""
        # Crear evento sin ubicación
        event = Event.objects.create(
            title="Evento sin ubicación",
            description="Descripción del evento",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer
        )

        # Verificar que no hay entradas disponibles
        self.assertEqual(event.tickets_available, 0)
        # Verificar que la ocupación es 0%
        self.assertEqual(event.occupancy_percentage, 0.0)
        # Verificar que la demanda es baja
        self.assertEqual(event.demand_status, "Baja demanda") 