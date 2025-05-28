from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from app.models import Event, User, Venue, Category
import datetime

class EventE2ETest(TestCase):
    def setUp(self):
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.event_create_url = reverse("event_form")
        self.venue = Venue.objects.create(
            name="Venue Test",
            address="Calle Falsa 123",
            city="Springfield",
            capacity=100,
            contact="contacto@example.com"
        )
        self.category = Category.objects.create(name="Categoría prueba")
    
    def test_full_event_flow(self):
        # 1. Registro usuario organizador
        user_data = {
            "email": "organizer@example.com",
            "username": "organizer",
            "is-organizer": "on",  # checkbox present
            "password": "strongpass123",
            "password-confirm": "strongpass123",
        }
        response = self.client.post(self.register_url, user_data)
        self.assertEqual(response.status_code, 302)  # Redirect after register

        # 2. Login usuario organizador (no siempre necesario porque auto login en register, pero hacemos para el flujo)
        login_data = {
            "username": "organizer",
            "password": "strongpass123",
        }
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, 302)  # Redirect after login

        # 3. Crear evento sin estado para que se asigne 'active' automáticamente
        future_date = (timezone.now() + datetime.timedelta(days=10)).date().isoformat()
        create_event_data = {
            "title": "Evento de prueba",
            "description": "Descripción del evento",
            "date": future_date,
            "time": "20:00",
            "categories": [self.category.id],  # type: ignore
             "venue": self.venue.id, # type: ignore
            # No se envía 'status' para probar que se asigne 'active' por defecto
        }
        response = self.client.post(self.event_create_url, create_event_data)
        
        self.assertEqual(response.status_code, 302)  # Redirect después de crear

        event = Event.objects.get(title="Evento de prueba")
        self.assertEqual(event.status, "active")

        # 4. Editar evento cambiando fecha para que cambie estado a 'rescheduled'
        new_future_date = (timezone.now() + datetime.timedelta(days=20)).date().isoformat()
        edit_url = reverse("event_edit", kwargs={"id": event.id}) # type: ignore
        edit_data = {
            "title": event.title,
            "description": event.description,
            "date": new_future_date,
            "time": "20:00",
            "status": event.status,  # mantenemos el estado para que update_status detecte cambio fecha
             "categories": [self.category.id],  # type: ignore
             "venue": self.venue.id, # type: ignore
        }
        response = self.client.post(edit_url, edit_data)
        self.assertEqual(response.status_code, 302)

        event.refresh_from_db()
        self.assertEqual(event.status, "rescheduled")

        # 5. Modificar estado a 'sold_out'
        sold_out_data = {
            "title": event.title,
            "description": event.description,
            "date": new_future_date,
            "time": "20:00",
            "status": "sold_out",
            "categories": [self.category.id],  # type: ignore
             "venue": self.venue.id, # type: ignore
            
        }
        response = self.client.post(edit_url, sold_out_data)
        self.assertEqual(response.status_code, 302)

        event.refresh_from_db()
        self.assertEqual(event.status, "sold_out")
