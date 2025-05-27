from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
import datetime

from app.models import Event, User, Venue, Category

class EventFilterIntegrationTest(TestCase):
    """Tests de integración para la funcionalidad de filtrado de eventos"""

    def setUp(self):
        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador_filter",
            email="organizador_filter@example.com",
            password="password123",
            is_organizer=True,
        )

        # Crear usuario regular
        self.regular_user = User.objects.create_user(
            username="usuario_filter",
            email="usuario_filter@example.com",
            password="password123",
            is_organizer=False,
        )

        # Crear venue y categoría
        self.venue = Venue.objects.create(
            name="Venue de prueba filter",
            adress="Dirección de prueba",
            city="Ciudad de prueba",
            capacity=100,
            contact="contacto@prueba.com"
        )

        self.category = Category.objects.create(
            name="Categoría de prueba filter",
            description="Descripción de la categoría de prueba",
            is_active=True
        )

        # Crear eventos con diferentes fechas
        # Evento pasado
        past_date = timezone.now() - datetime.timedelta(days=1)
        self.past_event = Event.objects.create(
            title="Evento pasado",
            description="Descripción del evento pasado",
            scheduled_at=past_date,
            organizer=self.organizer,
            venue=self.venue,
            category=self.category
        )

        # Evento actual (en la próxima hora)
        current_date = timezone.now() + datetime.timedelta(minutes=30)
        self.current_event = Event.objects.create(
            title="Evento actual",
            description="Descripción del evento actual",
            scheduled_at=current_date,
            organizer=self.organizer,
            venue=self.venue,
            category=self.category
        )

        # Evento futuro
        future_date = timezone.now() + datetime.timedelta(days=10)
        self.future_event = Event.objects.create(
            title="Evento futuro",
            description="Descripción del evento futuro",
            scheduled_at=future_date,
            organizer=self.organizer,
            venue=self.venue,
            category=self.category
        )

        # Crear cliente para las pruebas
        self.client = Client()

    def test_events_list_view_shows_only_future_events(self):
        """Test que verifica que la vista de lista de eventos solo muestra eventos futuros"""
        # Iniciar sesión como usuario regular
        self.client.login(username="usuario_filter", password="password123")
        
        # Obtener la respuesta de la vista
        response = self.client.get(reverse('events'))
        
        # Verificar que la respuesta es exitosa
        self.assertEqual(response.status_code, 200)
        
        # Verificar que solo se muestran los eventos futuros
        self.assertNotContains(response, "Evento pasado")
        self.assertContains(response, "Evento actual")
        self.assertContains(response, "Evento futuro")

    def test_events_list_view_ordered_by_date(self):
        """Test que verifica que los eventos están ordenados por fecha en la vista"""
        # Iniciar sesión como usuario regular
        self.client.login(username="usuario_filter", password="password123")
        
        # Obtener la respuesta de la vista
        response = self.client.get(reverse('events'))
        
        # Obtener el contenido de la respuesta
        content = response.content.decode()
        
        # Encontrar las posiciones de los eventos en el contenido
        current_pos = content.find("Evento actual")
        future_pos = content.find("Evento futuro")
        
        # Verificar que el evento actual aparece antes que el futuro
        self.assertLess(current_pos, future_pos)

    def test_events_list_view_no_events_message(self):
        """Test que verifica que se muestra el mensaje correcto cuando no hay eventos futuros"""
        # Eliminar todos los eventos
        Event.objects.all().delete()
        
        # Iniciar sesión como usuario regular
        self.client.login(username="usuario_filter", password="password123")
        
        # Obtener la respuesta de la vista
        response = self.client.get(reverse('events'))
        
        # Verificar que se muestra el mensaje de no hay eventos
        self.assertContains(response, "No hay eventos disponibles") 