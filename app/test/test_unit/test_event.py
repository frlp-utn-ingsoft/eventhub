from datetime import date, time, timedelta
import datetime
from django.test import TestCase
from django.utils import timezone
from app.forms import EventForm
from app.models import Event, User, Venue, Category


class TestEvent(TestCase):

    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador_test",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )
        self.venue = Venue.objects.create(
            name="Auditorio Test",
            address="Calle Falsa 123",
            capacity=100 
        )
        self.category = Category.objects.create(name="Música")
        self.event = Event.objects.create(
            title="Evento original",
            description="Descripción original",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue
        )

    def test_event_creation(self):
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue, 
            status="activo",
        )
        self.assertEqual(event.title, "Evento de prueba")
        self.assertEqual(event.description, "Descripción del evento de prueba")
        self.assertEqual(event.organizer, self.organizer)
        self.assertEqual(event.venue, self.venue)
        self.assertEqual(event.status, "activo")
        self.assertIsNotNone(event.created_at)
        self.assertIsNotNone(event.updated_at)

    def test_event_form_valid_data(self):
        form_data = {
            'title': 'Concierto de Jazz',
            'description': 'Un evento musical al aire libre.',
            'date': date.today() + timedelta(days=1),
            'time': '19:30',
            'categories': [self.category.id],#type:ignore
            'venue': self.venue.id #type:ignore
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_event_form_invalid_empty_title(self):
        """Verifica que el formulario detecta título vacío"""
        data = {
            "title": "",
            "description": "Descripción válida",
            "date": datetime.date.today() + datetime.timedelta(days=1),
            "time": datetime.time(12, 0),
            "categories": [1],
            "venue": 1
        }

        form = EventForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)
        self.assertIn("Este campo es obligatorio.", form.errors["title"])

    def test_event_form_invalid_empty_description(self):
        """Verifica que el formulario detecta descripción vacía"""
        data = {
            "title": "Título válido",
            "description": "",
            "date": datetime.date.today() + datetime.timedelta(days=1),
            "time": datetime.time(12, 0),
            "categories": [1],
            "venue": 1
        }

        form = EventForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("description", form.errors)
        self.assertIn("Este campo es obligatorio.", form.errors["description"])

  
    def test_event_new_with_valid_data(self):
        """Verifica la creación de un nuevo evento con datos válidos a través del formulario."""
        
        # Define una fecha en el futuro para el evento
        future_date = timezone.localdate() + datetime.timedelta(days=7) 
        
        data = {
            "title": "Nuevo Evento de Prueba",
            "description": "Descripción para el nuevo evento.",
            "date": future_date,
            "time": datetime.time(18, 0), 
            "categories": [self.category.id], #type: ignore
            "venue": self.venue.id, #type: ignore
            "organizer": self.organizer.id, #type: ignore
        }

        # Cuenta los eventos antes de crear el nuevo
        initial_event_count = Event.objects.count()

        form = EventForm(data=data)
        
        # El formulario debe ser válido
        self.assertTrue(form.is_valid())

        # Guarda la instancia del modelo (new_event) sin guardar aún las relaciones Many-to-Many
        new_event = form.save(commit=False) 
        
        new_event.organizer = self.organizer 
        
        # Guarda la instancia principal en la base de datos para que tenga un ID
        new_event.save() 
        
        # Guarda las relaciones Many-to-Many
        form.save_m2m() 

        
        self.assertEqual(Event.objects.count(), initial_event_count + 1)
        
        # Verifica que el nuevo evento tenga los datos correctos
        self.assertEqual(new_event.title, data["title"])
        self.assertEqual(new_event.description, data["description"])
        self.assertEqual(new_event.scheduled_at.date(), data["date"])
        self.assertEqual(new_event.scheduled_at.time(), data["time"])
        self.assertEqual(new_event.organizer, self.organizer)
        self.assertEqual(new_event.venue, self.venue)
        
        # Ahora, verifica que la categoría se haya asociado correct

    def test_event_form_with_invalid_data(self):
        """Test que verifica que el formulario no es válido con datos inválidos"""

        scheduled_date = (timezone.now() + datetime.timedelta(days=2)).date()
        scheduled_time = (timezone.now() + datetime.timedelta(days=2)).time()

        form_data = {
            "title": "",  # título vacío (inválido)
            "description": "Descripción válida",
            "date": scheduled_date,
            "time": scheduled_time,
            "categories": [],  # suponiendo que es requerido
            "venue": None      # suponiendo que es requerido
        }

        form = EventForm(data=form_data)

        # El formulario no debería ser válido
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)
        self.assertIn("categories", form.errors)
        self.assertIn("venue", form.errors)

    def test_event_update_with_form(self):
        """Verifica que el evento se actualiza correctamente usando datos validados por el formulario"""
        data = {
            "title": "Título actualizado",
            "description": "Descripción actualizada",
            "date": (timezone.now() + datetime.timedelta(days=1)).date(),
            "time": datetime.time(15, 0),
            "categories": [self.category.id], #type: ignore
            "venue": self.venue.id #type: ignore
        }

        form = EventForm(data=data, instance=self.event)
        self.assertTrue(form.is_valid())
        updated_event = form.save()

        self.assertEqual(updated_event.title, data["title"])
        self.assertEqual(updated_event.description, data["description"])
        self.assertEqual(updated_event.scheduled_at.date(), data["date"])
        self.assertEqual(updated_event.scheduled_at.time(), data["time"])

    def test_event_partial_update_with_form(self):
        """Verifica que el evento puede actualizar solo algunos campos"""
        # Solo cambia la descripción
        data = {
            "title": self.event.title,  # igual al original
            "description": "Descripción parcialmente actualizada",
            "date": self.event.scheduled_at.date(),
            "time": self.event.scheduled_at.time(),
            "categories": [self.category.id], #type: ignore
            "venue": self.venue.id #type: ignore
        }

        form = EventForm(data=data, instance=self.event)
        self.assertTrue(form.is_valid())
        updated_event = form.save()

        self.assertEqual(updated_event.title, self.event.title)
        self.assertEqual(updated_event.description, "Descripción parcialmente actualizada")
        self.assertEqual(updated_event.scheduled_at, self.event.scheduled_at) 
