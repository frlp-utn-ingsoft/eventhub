from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import make_aware
from datetime import datetime
from app.models import User, Event, Venue, Category

class EventStatusIntegrationTest(TestCase):
    def setUp(self):
        # Crear usuario con permiso para organizar eventos
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.user.is_organizer = True
        self.user.save()

        # Crear venue
        self.venue = Venue.objects.create(
            name="Venue Test",
            address="Calle Falsa 123",
            city="Springfield",
            capacity=100,
            contact="contacto@example.com"
        )
        self.category = Category.objects.create(name="Categoría prueba")

        # Fecha original
        self.original_date = make_aware(datetime(2025, 12, 25, 18, 0))

        # Crear evento con estado activo
        self.event = Event.objects.create(
            title="Evento Test",
            description="Descripción del evento",
            scheduled_at=self.original_date,
            organizer=self.user,
            venue=self.venue,
            status="active"
        )

        # Login usuario para usar client
        self.client.login(username="testuser", password="testpass")

    def test_event_status_changes_to_rescheduled_on_date_change(self):
        # URL para editar evento
        url = reverse("event_edit", kwargs={"id": self.event.id}) # type: ignore

        # Nuevo data con fecha distinta (para disparar cambio de estado)
        data = {
            "title": "Evento Test Editado",
            "description": "Descripción actualizada",
            "date": "2025-12-31",  # diferente a original
            "time": "20:00",
            "status": "active",  # aunque venga active, el método update_status debe cambiarlo a rescheduled
            "venue": self.venue.id, # type: ignore
            "categories": [self.category.id], # type: ignore
        }

        response = self.client.post(url, data)

        updated_event = Event.objects.get(id=self.event.id) # type: ignore
        self.assertEqual(updated_event.status, "rescheduled")


        # También podés chequear que la respuesta sea un redirect (200 es otro caso)
        self.assertEqual(response.status_code, 302)
