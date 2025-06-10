from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from app.models import Event
from app.views import events


class EventListViewTest(TestCase):
    """Tests unitarios para la vista de eventos"""

    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_organizer=True
        )
        
        # Crear eventos de prueba
        now = timezone.now()
        self.future_event = Event.objects.create(
            title="Evento Futuro",
            description="Descripción del evento futuro",
            scheduled_at=now + timedelta(days=30),
            organizer=self.user
        )
        
        self.past_event = Event.objects.create(
            title="Evento Pasado",
            description="Descripción del evento pasado",
            scheduled_at=now - timedelta(days=1),
            organizer=self.user
        )

        # Iniciar sesión como el usuario de prueba
        self.client.login(username='testuser', password='testpass123')

    def test_filter_past_events(self):
        """Test que verifica que por defecto solo se muestran eventos futuros"""
        response = self.client.get('/events/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('events', response.context)
        events_list = response.context['events']
        
        # Verificar que solo se muestra el evento futuro
        self.assertEqual(events_list.count(), 1)
        self.assertEqual(events_list[0], self.future_event)
        
        # Verificar que el toggle está desactivado
        self.assertFalse(response.context['show_past'])

    def test_show_past_events(self):
        """Test que verifica que se muestran todos los eventos cuando se activa el toggle"""
        response = self.client.get('/events/?show_past=true')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('events', response.context)
        events_list = response.context['events']
        
        # Verificar que se muestran ambos eventos
        self.assertEqual(events_list.count(), 2)
        
        # Verificar que el toggle está activado
        self.assertTrue(response.context['show_past'])

    def test_event_ordering(self):
        """Test que verifica el ordenamiento de los eventos"""
        response = self.client.get('/events/?show_past=true')
        events_list = response.context['events']
        
        # Verificar que los eventos están ordenados por fecha descendente
        self.assertEqual(events_list[0], self.future_event)
        self.assertEqual(events_list[1], self.past_event) 