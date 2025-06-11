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
        self.venue = Venue.objects.create(name="Lugar 1", capacity=2) ## 2 de capacidad
        # Crear evento de prueba
        self.event = Event.objects.create(
            title="Evento 1",
            description="Descripción del evento 1",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
        )
        # Crear usuarios para los tickets
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
        """Test de integración que verifica que la vista event_detail muestra la demanda correctamente y si es alta o baja"""
        # Login como organizador
        self.client.login(username="organizador", password="password123")

        # Demanda baja (sin tickets)
        response = self.client.get(reverse("event_detail", args=[self.event.id]))
        self.assertContains(response, "Baja demanda")
        self.assertContains(response, "0") #0 entradas vendidas

        #Demanda alta (con 100% de tickets vendidos)
        Ticket.objects.create(user=self.user1, event=self.event, type="general", quantity=1)
        Ticket.objects.create(user=self.user2, event=self.event, type="general", quantity=1)
        response = self.client.get(reverse("event_detail", args=[self.event.id]))
        self.assertContains(response, "Alta demanda")
        self.assertContains(response, "2") #2 entradas vendidas

        