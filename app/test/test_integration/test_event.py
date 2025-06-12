import datetime
import time

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import Category, Event, User, Venue


class BaseEventTestCase(TestCase):
    def setUp(self):
        # Crear usuario organizador antes de usarlo
        self.organizer = User.objects.create_user(
            username="organizador",
            password="password123",
            is_organizer=True
        )
        # Crear usuario regular para otros tests si es necesario
        self.regular_user = User.objects.create_user(
            username="regular",
            password="password123",
            is_organizer=False
        )
        
        # Usar valores válidos para status
        self.event1 = Event.objects.create(
            title="Evento 1",
            description="Descripción del evento 1",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            status='activo'  # Valor válido
        )

        self.event2 = Event.objects.create(
            title="Evento 2",
            description="Descripción del evento 2",
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            organizer=self.organizer,
            status='activo' 
        )

        # Cliente para hacer peticiones
        self.client = Client()


class EventsListViewTest(BaseEventTestCase):
    """Tests para la vista de listado de eventos"""
    # ... (código existente sin cambios) ...


class EventDetailViewTest(BaseEventTestCase):
    """Tests para la vista de detalle de un evento"""
    # ... (código existente sin cambios) ...


class EventFormViewTest(BaseEventTestCase):
    """Tests para la vista del formulario de eventos"""
    
    def test_event_form_view_with_organizer(self):
        """Test que verifica que la vista event_form funciona cuando el usuario es organizador"""
        # Login con usuario organizador
        self.client.login(username="organizador", password="password123")

        # Usar vista de creación sin parámetros
        response = self.client.get(reverse("event_create"))

        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/event/event_form.html")
        self.assertIn("form", response.context)

    # ... (otros métodos sin cambios) ...


class EventFormSubmissionTest(BaseEventTestCase):
    """Tests para la creación y edición de eventos mediante POST"""

    def setUp(self):
        super().setUp()
        self.venue = Venue.objects.create(
            name="Test Venue",
            address="Test Address",
            city="Test City",
            capacity=100,
            contact_info="Test Contact",
            created_by=self.organizer
        )
        self.category = Category.objects.create(name="Test Category")

    def test_event_form_post_create(self):
        """Test que verifica que se puede crear un evento mediante POST"""
        # Login con usuario organizador
        self.client.login(username="organizador", password="password123")

        # Crear datos para el evento con estado válido
        event_data = {
            "title": "Nuevo Evento",
            "description": "Descripción del nuevo evento",
            "scheduled_at": "2025-10-31 14:30:00",
            "venue": self.venue.pk,
            "categories": [self.category.pk],
            "status": "activo"  
        }

        # Hacer petición POST a la vista event_form
        response = self.client.post(reverse("event_create"), event_data)

        # Verificar que redirecciona a events
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("events"))

        # Verificar que se creó el evento
        self.assertTrue(Event.objects.filter(title="Nuevo Evento").exists())
        evento = Event.objects.get(title="Nuevo Evento")
        self.assertEqual(evento.description, "Descripción del nuevo evento")
        self.assertEqual(evento.scheduled_at.year, 2025)
        self.assertEqual(evento.scheduled_at.month, 10)
        self.assertEqual(evento.scheduled_at.day, 31)
        self.assertEqual(evento.scheduled_at.hour, 14)
        self.assertEqual(evento.scheduled_at.minute, 30)
        self.assertEqual(evento.organizer, self.organizer)

    def test_event_form_post_edit(self):
        """Test que verifica que se puede editar un evento existente mediante POST"""
        # Login con usuario organizador
        self.client.login(username="organizador", password="password123")

        # Datos para actualizar el evento con estado válido
        updated_data = {
            "title": "Evento 1 Actualizado",
            "description": "Nueva descripción actualizada",
            "scheduled_at": "2025-08-12 17:30:00",
            "venue": self.venue.pk,
            "categories": [self.category.pk],
            "status": "activo"  
        }

        # Hacer petición POST para editar el evento
        response = self.client.post(
            reverse("event_edit", args=[self.event1.id]), 
            updated_data
        )

        # Verificar que redirecciona a events
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("events"))

        # Verificar que el evento fue actualizado
        self.event1.refresh_from_db()
        self.assertEqual(self.event1.title, "Evento 1 Actualizado")
        self.assertEqual(self.event1.description, "Nueva descripción actualizada")
        self.assertEqual(self.event1.scheduled_at.year, 2025)
        self.assertEqual(self.event1.scheduled_at.month, 8)
        self.assertEqual(self.event1.scheduled_at.day, 12)
        self.assertEqual(self.event1.scheduled_at.hour, 17)
        self.assertEqual(self.event1.scheduled_at.minute, 30)


class EventDeleteViewTest(BaseEventTestCase):
    """Tests para la eliminación de eventos"""
    
    def test_event_delete_with_organizer(self):
        """Test que verifica que un organizador puede eliminar un evento"""
        # Iniciar sesión como organizador
        self.client.login(username="organizador", password="password123")

        # Verificar que el evento existe antes de eliminar
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())

        # Usar id en lugar de event_id
        response = self.client.post(reverse("event_delete", args=[self.event1.id]))

        # Verificar que redirecciona a la página de eventos
        self.assertRedirects(response, reverse("events"))

        # Verificar que el evento ya no existe
        self.assertFalse(Event.objects.filter(pk=self.event1.id).exists())



    def test_event_delete_with_regular_user(self):
        """Test que verifica que un usuario regular no puede eliminar un evento"""
        # Iniciar sesión como usuario regular
        self.client.login(username="regular", password="password123")

        # Verificar que el evento existe antes de intentar eliminarlo
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())

        # Hacer una petición POST para intentar eliminar el evento
        response = self.client.post(reverse("event_delete", args=[self.event1.id]))

        # Verificar que redirecciona a la página de eventos sin eliminar
        self.assertRedirects(response, reverse("events"))

        # Verificar que el evento sigue existiendo
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())

    def test_event_delete_with_get_request(self):
        """Test que verifica que la vista redirecciona si se usa GET en lugar de POST"""
        # Iniciar sesión como organizador
        self.client.login(username="organizador", password="password123")

        # Hacer una petición GET para intentar eliminar el evento
        response = self.client.get(reverse("event_delete", args=[self.event1.id]))

        # Verificar que redirecciona a la página de eventos
        self.assertRedirects(response, reverse("events"))

        # Verificar que el evento sigue existiendo
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())

    def test_event_delete_nonexistent_event(self):
        """Test que verifica el comportamiento al intentar eliminar un evento inexistente"""
        # Iniciar sesión como organizador
        self.client.login(username="organizador", password="password123")

        # ID inexistente
        nonexistent_id = 9999

        # Verificar que el evento con ese ID no existe
        self.assertFalse(Event.objects.filter(pk=nonexistent_id).exists())

        # Hacer una petición POST para eliminar el evento inexistente
        response = self.client.post(reverse("event_delete", args=[nonexistent_id]))

        # Verificar que devuelve error 404
        self.assertEqual(response.status_code, 404)

    def test_event_delete_without_login(self):
        """Test que verifica que la vista redirecciona a login si el usuario no está autenticado"""
        # Verificar que el evento existe antes de intentar eliminarlo
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())

        # Hacer una petición POST sin iniciar sesión
        response = self.client.post(reverse("event_delete", args=[self.event1.id]))

        # Verificar que redirecciona al login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

        # Verificar que el evento sigue existiendo
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())