from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from app.models import Event, User


class EventListIntegrationTest(TestCase):
    """Tests de integración para la lista de eventos"""

    def setUp(self):
        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )

        # Crear usuario regular
        self.regular_user = User.objects.create_user(
            username="usuario",
            email="usuario@example.com",
            password="password123",
            is_organizer=False,
        )

        # Crear eventos de prueba usando fechas relativas a now()
        now = timezone.now()
        
        # Evento futuro (1 mes adelante)
        event_date1 = now + timedelta(days=30)
        self.event1 = Event.objects.create(
            title="Evento de prueba 1",
            description="Descripción del evento 1",
            scheduled_at=event_date1,
            organizer=self.organizer,
        )

        # Evento pasado (1 día atrás)
        event_date2 = now - timedelta(days=1)
        self.event2 = Event.objects.create(
            title="Evento de prueba 2",
            description="Descripción del evento 2",
            scheduled_at=event_date2,
            organizer=self.organizer,
        )

        # Crear cliente para hacer peticiones
        self.client = Client()

    def test_events_list_default_view(self):
        """Test que verifica que por defecto solo se muestran eventos futuros"""
        # Iniciar sesión como usuario regular
        self.client.login(username="usuario", password="password123")
        
        # Hacer la petición GET a la vista de eventos
        response = self.client.get(reverse('events'))
        
        # Verificar que la respuesta es exitosa
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el contexto contiene los eventos
        self.assertIn('events', response.context)
        
        # Verificar que solo se muestra el evento futuro
        events_list = response.context['events']
        self.assertEqual(events_list.count(), 1)
        self.assertEqual(events_list[0], self.event1)
        
        # Verificar que el toggle está desactivado
        self.assertFalse(response.context['show_past'])

    def test_events_list_with_past_events(self):
        """Test que verifica que se pueden mostrar eventos pasados"""
        # Iniciar sesión como usuario regular
        self.client.login(username="usuario", password="password123")
        
        # Hacer la petición GET a la vista de eventos con show_past=true
        response = self.client.get(reverse('events'), {'show_past': 'true'})
        
        # Verificar que la respuesta es exitosa
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el contexto contiene los eventos
        self.assertIn('events', response.context)
        
        # Verificar que se muestran todos los eventos
        events_list = response.context['events']
        self.assertEqual(events_list.count(), 2)
        
        # Verificar que el toggle está activado
        self.assertTrue(response.context['show_past'])

    def test_events_list_ordering(self):
        """Test que verifica el ordenamiento de eventos"""
        # Iniciar sesión como usuario regular
        self.client.login(username="usuario", password="password123")
        
        # Hacer la petición GET a la vista de eventos con show_past=true
        response = self.client.get(reverse('events'), {'show_past': 'true'})
        
        # Verificar que la respuesta es exitosa
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el contexto contiene los eventos
        self.assertIn('events', response.context)
        
        # Verificar que los eventos están ordenados por fecha descendente
        events_list = response.context['events']
        self.assertEqual(events_list[0], self.event1)  # Evento futuro primero
        self.assertEqual(events_list[1], self.event2)  # Evento pasado después 