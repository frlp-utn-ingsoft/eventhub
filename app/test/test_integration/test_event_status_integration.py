import datetime
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from app.models import Event, User
from category.models import Category

class EventStatusIntegrationTest(TestCase):
    """
    Tests de integración específicos para la gestión del status de eventos.
    """

    def setUp(self):
        self.client = Client()

        self.organizer = User.objects.create_user(
            username="organizador_status_int",
            email="organizador.status@test.com",
            password="password123",
            is_organizer=True,
        )
        self.category_music = Category.objects.create(name='Music Status Int', is_active=True)
        self.category_sports = Category.objects.create(name='Sports Status Int', is_active=True)

        self.event_to_edit = Event.objects.create(
            title="Event to Edit Status Int",
            description="Original description for status edit.",
            scheduled_at=timezone.now() + datetime.timedelta(days=5),
            organizer=self.organizer,
            status='activo'
        )
        self.event_to_edit.categories.add(self.category_music)

    def test_create_event_with_specific_status_as_organizer(self):
        """
        Verifica que un organizador puede crear un evento y asignarle un status específico.
        """
        self.client.login(username=self.organizer.username, password="password123")

        event_date = (timezone.now() + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
        event_time = (timezone.now() + datetime.timedelta(days=7)).strftime('%H:%M')

        response = self.client.post(reverse('event_form'), {
            'title': 'Integration Test Event with Status',
            'description': 'Description for new event with status.',
            'date': event_date,
            'time': event_time,
            'categories': [self.category_music.id],
            'status': 'reprogramado', 
        })

        self.assertEqual(response.status_code, 302) 
        event = Event.objects.get(title='Integration Test Event with Status')
        self.assertIsNotNone(event)
        self.assertEqual(event.status, 'reprogramado') 

    def test_edit_event_status_as_organizer(self):
        """
        Verifica que un organizador puede editar el status de un evento existente.
        """
        self.client.login(username=self.organizer.username, password="password123")

        event_date = self.event_to_edit.scheduled_at.strftime('%Y-%m-%d')
        event_time = self.event_to_edit.scheduled_at.strftime('%H:%M')

        response = self.client.post(reverse('event_edit', args=[self.event_to_edit.id]), {
            'title': 'Event to Edit Status Int', 
            'description': 'Updated description for status test.',
            'date': event_date,
            'time': event_time,
            'categories': [self.category_sports.id],
            'status': 'agotado', 
        })

        self.assertEqual(response.status_code, 302) 
        self.event_to_edit.refresh_from_db() 
        self.assertEqual(self.event_to_edit.status, 'agotado') 

    def test_event_status_default_on_creation(self):
        """
        Verifica que si no se especifica el status, se guarda como 'activo' por defecto.
        """
        self.client.login(username=self.organizer.username, password="password123")

        event_date = (timezone.now() + datetime.timedelta(days=8)).strftime('%Y-%m-%d')
        event_time = (timezone.now() + datetime.timedelta(days=8)).strftime('%H:%M')

        response = self.client.post(reverse('event_form'), {
            'title': 'Default Status Event',
            'description': 'Event with default status.',
            'date': event_date,
            'time': event_time,
            'categories': [self.category_music.id],
        })

        self.assertEqual(response.status_code, 302)
        event = Event.objects.get(title='Default Status Event')
        self.assertEqual(event.status, 'activo') 