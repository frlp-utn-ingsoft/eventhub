import datetime

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from app.models import Event, User, Venue, Ticket


class BaseEventTestCase(TestCase):
    """Clase base con la configuración común para todos los tests de eventos"""

    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )

        self.not_organizer = User.objects.create_user(
            username="not_organizer",
            email="not_organizer@test.com",
            password="password123",
            is_organizer=True,
        )

        self.regular = User.objects.create_user(
            username="regular",
            email="regular@test.com",
            password="password123",
            is_organizer=False,
        )

        self.venue_mocked = Venue.objects.create(
            name='Auditorio UTN',
            address='Av. Siempreviva 742',
            capacity=200
        )

        self.event_mocked = Event.objects.create(
            title="Evento 1",
            description="Descripción del evento 1",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue_mocked
        )

        self.client = Client()

    def test_organizer_sees_ticket_data_and_demand_message(self):
        self.client.login(username="organizador", password="password123")
        Ticket.objects.create(user=self.not_organizer, event=self.event_mocked, quantity=950, type="general")
        response = self.client.get(reverse("event_detail", args=[self.event_mocked.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/event_detail.html")
        self.assertContains(response, "950")
        self.assertContains(response, "ALTA")


    def test_not_organizer_does_not_see_ticket_data_and_demand_message(self):
        self.client.login(username="not_organizer", password="password123")
        Ticket.objects.create(user=self.not_organizer, event=self.event_mocked, quantity=950, type="general")
        response = self.client.get(reverse("event_detail", args=[self.event_mocked.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/event_detail.html")
        self.assertNotContains(response, "950")
        self.assertNotContains(response, "ALTA")
        self.assertNotContains(response, "MEDIA")
        self.assertNotContains(response, "BAJA")

    def test_regular_user_does_not_see_ticket_data_and_demand_message(self):
        self.client.login(username="regular", password="password123")
        Ticket.objects.create(user=self.regular, event=self.event_mocked, quantity=950, type="general")
        response = self.client.get(reverse("event_detail", args=[self.event_mocked.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/event_detail.html")
        self.assertNotContains(response, "950")
        self.assertNotContains(response, "ALTA")
        self.assertNotContains(response, "MEDIA")
        self.assertNotContains(response, "BAJA")    