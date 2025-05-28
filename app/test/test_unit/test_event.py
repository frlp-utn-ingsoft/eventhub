from django.test import TestCase
from django.utils import timezone
from app.models import Event, Venue, User  # Ajusta imports según tu estructura
import datetime

from app.models import Event, User


    def setUp(self):
        self.organizer = User.objects.create_user(username="organizer", password="pass")
        self.venue = Venue.objects.create(name="Test Venue", capacity=100)
        
        # Crear un venue para las pruebas
        self.venue = Venue.objects.create(
            name="Venue de prueba",
            adress="Dirección de prueba",
            city="Ciudad de prueba",
            capacity=100,
            contact="contacto@prueba.com"
        )

    def test_default_state_is_active(self):
        event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
        )
        self.assertEqual(event.state, Event.ACTIVE)

    def test_event_new_with_valid_data(self):
        """Test que verifica la creación de eventos con datos válidos"""
        scheduled_at = timezone.now() + datetime.timedelta(days=2)
        success, result = Event.new(
            title="Nuevo evento",
            description="Descripción del nuevo evento",
            scheduled_at=scheduled_at,
            organizer=self.organizer,
            venue=self.venue
        )

        self.assertTrue(success)
        self.assertIsInstance(result, Event)

        # Verificar que el evento fue creado en la base de datos
        new_event = Event.objects.get(title="Nuevo evento")
        self.assertEqual(new_event.description, "Descripción del nuevo evento")
        self.assertEqual(new_event.organizer, self.organizer)
        self.assertEqual(new_event.venue, self.venue)

    def test_event_new_with_invalid_data(self):
        """Test que verifica que no se crean eventos con datos inválidos"""
        scheduled_at = timezone.now() + datetime.timedelta(days=2)
        initial_count = Event.objects.count()

        # Intentar crear evento con título vacío
        success, errors = Event.new(
            title="",
            description="Descripción del evento",
            scheduled_at=scheduled_at,
            organizer=self.organizer,
            venue=self.venue
        )

        self.assertFalse(success)
        self.assertIn("title", errors)

        # Verificar que no se creó ningún evento nuevo
        self.assertEqual(Event.objects.count(), initial_count)

    def test_event_update(self):
        """Test que verifica la actualización de eventos"""
        new_title = "Título actualizado"
        new_description = "Descripción actualizada"
        new_scheduled_at = timezone.now() + datetime.timedelta(days=3)

    def test_update_event_sets_reprogramed_if_date_changes(self):
        event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue
            venue=self.venue,
        )

        event.update(
            title=new_title,
            description=new_description,
            scheduled_at=new_scheduled_at,
            organizer=self.organizer,
            venue=self.venue
            venue=self.venue,
        )
        event.auto_update_state()
        self.assertEqual(event.state, Event.FINISHED)
        self.assertEqual(updated_event.venue, self.venue)

    def test_auto_update_state_sets_sold_out_if_no_tickets_available(self):
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue
        )

        original_title = event.title
        original_scheduled_at = event.scheduled_at
        new_description = "Solo la descripción ha cambiado"

        event.update(
            title=None,  # No cambiar
            description=new_description,
            scheduled_at=None,  # No cambiar
            organizer=None,  # No cambiar
            venue=None  # No cambiar
        )

        # Recargar el evento desde la base de datos
        updated_event = Event.objects.get(pk=event.pk)

        # Verificar que solo cambió la descripción
        self.assertEqual(updated_event.title, original_title)
        self.assertEqual(updated_event.description, new_description)
        self.assertEqual(updated_event.scheduled_at, original_scheduled_at)
        self.assertEqual(updated_event.venue, self.venue)
    

    def test_event_favorite_functionality(self):
        """Test que verifica la funcionalidad de marcar/desmarcar favoritos"""
        # Crear un usuario regular
        regular_user = User.objects.create_user(
            username="usuario_test",
            email="usuario@test.com",
            password="password123",
            is_organizer=False,
        )

        # Crear un evento
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue
        )

        # Verificar que inicialmente no está en favoritos
        self.assertFalse(event.favorited_by.filter(id=regular_user.id).exists())

        # Agregar a favoritos
        event.favorited_by.add(regular_user)
        self.assertTrue(event.favorited_by.filter(id=regular_user.id).exists())

        # Quitar de favoritos
        event.favorited_by.remove(regular_user)
        self.assertFalse(event.favorited_by.filter(id=regular_user.id).exists())

            venue=self.venue,
        )
        # Simulamos que no hay tickets disponibles, seteamos a 0
        def fake_available_tickets():
            return 0
        event.available_tickets = fake_available_tickets
        event.auto_update_state()
        self.assertEqual(event.state, Event.SOLD_OUT)
