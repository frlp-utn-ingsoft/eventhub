import datetime
import time

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import Event, User


class BaseEventTestCase(TestCase):
    """Clase base con la configuración común para todos los tests de eventos"""

    def setUp(self):
        # Crear un usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )

        # Crear un usuario regular
        self.regular_user = User.objects.create_user(
            username="regular",
            email="regular@test.com",
            password="password123",
            is_organizer=False,
        )

        # Crear algunos eventos de prueba
        self.event1 = Event.objects.create(
            title="Evento 1",
            description="Descripción del evento 1",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            status='activo' # Agregado 'status'
        )

        self.event2 = Event.objects.create(
            title="Evento 2",
            description="Descripción del evento 2",
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            organizer=self.organizer,
            status='reprogramado' # Agregado 'status'
        )

        # Configurar cliente para pruebas HTTP
        self.client = Client()


class EventModelTest(TestCase):
    """Tests para la lógica del modelo Event, sin interacción con vistas ni estados específicos."""
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador_test",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )

    def test_event_creation(self):
        """Test que verifica la creación correcta de eventos, incluyendo el estado"""
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            status='activo'
        )
        self.assertEqual(event.title, "Evento de prueba")
        self.assertEqual(event.description, "Descripción del evento de prueba")
        self.assertEqual(event.organizer, self.organizer)
        self.assertEqual(event.status, 'activo')
        self.assertIsNotNone(event.created_at)
        self.assertIsNotNone(event.updated_at)

    def test_event_validate_with_valid_data(self):
        """Test que verifica la validación de eventos con datos válidos"""
        scheduled_at = timezone.now() + datetime.timedelta(days=1)
        errors = Event.validate("Título válido", "Descripción válida", scheduled_at)
        self.assertEqual(errors, {})

    def test_event_validate_with_missing_title(self):
        """Test que verifica la validación de eventos con título faltante"""
        scheduled_at = timezone.now() + datetime.timedelta(days=1)
        errors = Event.validate("", "Descripción válida", scheduled_at)
        self.assertIn("title", errors)
        self.assertEqual(errors["title"], "Por favor ingrese un titulo")

    def test_event_validate_with_missing_description(self):
        """Test que verifica la validación de eventos con descripción faltante"""
        scheduled_at = timezone.now() + datetime.timedelta(days=1)
        errors = Event.validate("Título válido", "", scheduled_at)
        self.assertIn("description", errors)
        self.assertEqual(errors["description"], "Por favor ingrese una descripcion")

    def test_event_new_with_valid_data(self):
        """Test que verifica la creación de un nuevo evento a través del método 'new' con datos válidos"""
        title = "Nuevo Evento Test"
        description = "Descripción del nuevo evento test"
        scheduled_at = timezone.now() + datetime.timedelta(days=7)
        status = 'finalizado' # status de prueba

        success, errors = Event.new(title, description, scheduled_at, self.organizer, status)

        self.assertTrue(success)
        self.assertIsNone(errors)
        self.assertTrue(
            Event.objects.filter(
                title=title, description=description, scheduled_at=scheduled_at, organizer=self.organizer, status=status
            ).exists()
        )

    def test_event_new_with_invalid_data(self):
        """Test que verifica la creación de un nuevo evento a través del método 'new' con datos inválidos"""
        title = ""
        description = "Descripción inválida"
        scheduled_at = timezone.now() + datetime.timedelta(days=7)
        status = 'activo' # status de prueba

        success, errors = Event.new(title, description, scheduled_at, self.organizer, status)

        self.assertFalse(success)
        self.assertIsNotNone(errors)
        self.assertIn("title", errors)
        self.assertFalse(
            Event.objects.filter(
                title=title, description=description, scheduled_at=scheduled_at, organizer=self.organizer
            ).exists()
        )

    def test_event_update_full(self):
        """Test que verifica la actualización completa de un evento existente"""
        event = Event.objects.create(
            title="Evento Original",
            description="Descripción original",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            status='activo' # status de prueba
        )

        new_title = "Evento Actualizado"
        new_description = "Nueva descripción actualizada"
        new_scheduled_at = timezone.now() + datetime.timedelta(days=5)
        new_status = 'cancelado' # nuevo status

        event.update(
            title=new_title,
            description=new_description,
            scheduled_at=new_scheduled_at,
            organizer=self.organizer,
            status=new_status 
        )

        updated_event = Event.objects.get(pk=event.pk)

        self.assertEqual(updated_event.title, new_title)
        self.assertEqual(updated_event.description, new_description)
        # Comparar fechas y horas ignorando microsegundos (evita errores de redondeo)
        self.assertEqual(updated_event.scheduled_at.replace(microsecond=0, second=0), new_scheduled_at.replace(microsecond=0, second=0))
        self.assertEqual(updated_event.status, new_status)


    def test_event_update_partial(self):
        """Test que verifica la actualización parcial de eventos"""
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            status='activo' # status de prueba
        )

        original_title = event.title
        original_scheduled_at = event.scheduled_at
        original_status = event.status # guardar el status original
        new_description = "Solo la descripción ha cambiado"

        event.update(
            title=None,
            description=new_description,
            scheduled_at=None,
            organizer=None,
            status=None, # no cambiar el status si es None
        )

        updated_event = Event.objects.get(pk=event.pk)

        self.assertEqual(updated_event.title, original_title)
        self.assertEqual(updated_event.description, new_description)
        self.assertEqual(updated_event.scheduled_at.replace(microsecond=0, second=0), original_scheduled_at.replace(microsecond=0, second=0))
        self.assertEqual(updated_event.status, original_status) # verificar que el status no cambió


class EventViewTests(BaseEventTestCase):
    """Tests para las vistas de eventos que requieren el cliente y eventos pre-creados."""

    def test_event_delete_successfully(self):
        """Test que verifica la eliminación exitosa de un evento"""
        self.client.login(username="organizador", password="password123")

        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())

        response = self.client.post(reverse("event_delete", args=[self.event1.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("events"))
        self.assertFalse(Event.objects.filter(pk=self.event1.id).exists())

    def test_event_delete_nonexistent_event(self):
        """Test que verifica el comportamiento al intentar eliminar un evento inexistente"""
        self.client.login(username="organizador", password="password123")

        nonexistent_id = 9999

        while Event.objects.filter(pk=nonexistent_id).exists():
            nonexistent_id += 1

        self.assertFalse(Event.objects.filter(pk=nonexistent_id).exists())

        response = self.client.post(reverse("event_delete", args=[nonexistent_id]))

        self.assertEqual(response.status_code, 404)

    def test_event_delete_without_login(self):
        """Test que verifica que la vista redirecciona a login si el usuario no está autenticado"""
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())

        response = self.client.post(reverse("event_delete", args=[self.event1.id]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))