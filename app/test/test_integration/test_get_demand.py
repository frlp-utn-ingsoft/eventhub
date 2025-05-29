import datetime
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from app.models import User, Event, Ticket, Venue, Category

class EventGetDemandIntegrationTest(TestCase):
    def setUp(self):
        # Crear un usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )
        # Crear venues
        self.venue1 = Venue.objects.create(name="Lugar 1", capacity=100)
        # Crear evento de prueba
        self.event1 = Event.objects.create(
            title="Evento 1",
            description="Descripción del evento 1",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue1,
        )

    def test_event_get_demand(self):
        """Test de integración que verifica que la vista event_detail muestra la demanda correctamente y si es alta o baja"""
        # Login como organizador
        self.client.login(username="organizador", password="password123")

        # Demanda baja (sin tickets)
        response = self.client.get(reverse("event_detail", args=[self.event1.id]))
        self.assertContains(response, "Baja demanda")

        # Crear 91 tickets para superar el 90% de ocupación (capacidad 100)
        for i in range(91):
            user = User.objects.create_user(
                username=f"user_{i}",
                email=f"user_{i}@test.com",
                password="password123"
            )
            Ticket.objects.create(
                user=user,
                event=self.event1,
                type="general",
                quantity=1
            )

        response = self.client.get(reverse("event_detail", args=[self.event1.id]))
        # Verificar que la cantidad de entradas vendidas es correcta == 91
        self.assertContains(response, "Entradas vendidas:")
        self.assertContains(response, "91")
        # Demanda alta
        self.assertContains(response, "Alta demanda")