from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
import datetime

from app.models import Event, User, Venue, Category

class EventStatesIntegrationTest(TestCase):
    """Tests de integración para la funcionalidad de estados de eventos"""

    def setUp(self):
        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador_states",
            email="organizador_states@example.com",
            password="password123",
            is_organizer=True,
        )

        # Crear usuario regular
        self.regular_user = User.objects.create_user(
            username="usuario_states",
            email="usuario_states@example.com",
            password="password123",
            is_organizer=False,
        )

        # Crear venue y categoría
        self.venue = Venue.objects.create(
            name="Venue de prueba states",
            adress="Dirección de prueba",
            city="Ciudad de prueba",
            capacity=100,
            contact="contacto@prueba.com"
        )

        self.category = Category.objects.create(
            name="Categoría de prueba states",
            description="Descripción de la categoría de prueba",
            is_active=True
        )

        # Crear evento
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
            category=self.category
        )

        # Crear cliente para las pruebas
        self.client = Client()

    def test_cancel_event_as_organizer(self):
        """Test que verifica que un organizador puede cancelar un evento"""
        # Iniciar sesión como organizador
        self.client.login(username="organizador_states", password="password123")
        
        # Intentar cancelar el evento
        response = self.client.post(reverse('event_canceled', args=[self.event.id]))
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)
        
        # Recargar el evento desde la base de datos
        self.event.refresh_from_db()
        
        # Verificar que el estado cambió a CANCELED
        self.assertEqual(self.event.state, Event.CANCELED)

    def test_cancel_event_as_regular_user(self):
        """Test que verifica que un usuario regular no puede cancelar un evento"""
        # Iniciar sesión como usuario regular
        self.client.login(username="usuario_states", password="password123")
        
        # Intentar cancelar el evento
        response = self.client.post(reverse('event_canceled', args=[self.event.id]))
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)
        
        # Recargar el evento desde la base de datos
        self.event.refresh_from_db()
        
        # Verificar que el estado NO cambió
        self.assertEqual(self.event.state, Event.ACTIVE)

    def test_edit_event_updates_state(self):
        """Test que verifica que editar un evento actualiza su estado"""
        # Iniciar sesión como organizador
        self.client.login(username="organizador_states", password="password123")
        
        # Datos para editar el evento
        new_date = (timezone.now() + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
        new_time = "15:00"
        
        # Editar el evento
        response = self.client.post(
            reverse('event_edit', args=[self.event.id]),
            {
                'title': self.event.title,
                'description': self.event.description,
                'date': new_date,
                'time': new_time,
                'venue': self.venue.id,
                'category': self.category.id
            }
        )
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)
        
        # Recargar el evento desde la base de datos
        self.event.refresh_from_db()
        
        # Verificar que el estado cambió a REPROGRAMED
        self.assertEqual(self.event.state, Event.REPROGRAMED)

    def test_events_list_shows_states(self):
        """Test que verifica que la lista de eventos muestra los estados correctamente"""
        # Iniciar sesión como organizador
        self.client.login(username="organizador_states", password="password123")
        
        # Obtener la página de eventos
        response = self.client.get(reverse('events'))
        
        # Verificar que la respuesta es exitosa
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el estado del evento aparece en la respuesta
        self.assertContains(response, self.event.get_state_display())

    def test_auto_update_states_in_list(self):
        """Test que verifica que los estados se actualizan automáticamente en la lista de eventos"""
        # Crear un evento pasado
        past_event = Event.objects.create(
            title="Evento pasado",
            description="Descripción del evento pasado",
            scheduled_at=timezone.now() - datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
            category=self.category
        )
        
        # Verificar que inicialmente está activo
        self.assertEqual(past_event.state, Event.ACTIVE)
        
        # Llamar al método de actualización automática
        past_event.auto_update_state()
        
        # Verificar que el estado cambió a FINISHED
        self.assertEqual(past_event.state, Event.FINISHED)
        
        # Iniciar sesión como organizador
        self.client.login(username="organizador_states", password="password123")
        
        # Obtener la página de eventos
        response = self.client.get(reverse('events'))
        
        # Verificar que la respuesta es exitosa
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el evento pasado no aparece en la lista (porque está filtrado)
        self.assertNotContains(response, "Evento pasado") 