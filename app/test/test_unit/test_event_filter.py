from django.test import TestCase
from django.utils import timezone
import datetime

from app.models import Event, User, Venue, Category

class EventFilterUnitTest(TestCase):
    """Tests unitarios para la funcionalidad de filtrado de eventos"""

    def setUp(self):
        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador_filter",
            email="organizador_filter@example.com",
            password="password123",
            is_organizer=True,
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

    def test_get_future_events(self):
        """Test que verifica que get_future_events() solo retorna eventos futuros"""
        future_events = Event.get_future_events()
        
        # Verificar que solo hay 2 eventos (actual y futuro)
        self.assertEqual(future_events.count(), 2)
        
        # Verificar que el evento pasado no está incluido
        self.assertNotIn(self.past_event, future_events)
        
        # Verificar que los eventos actual y futuro están incluidos
        self.assertIn(self.current_event, future_events)
        self.assertIn(self.future_event, future_events)

    def test_events_ordered_by_date(self):
        """Test que verifica que los eventos están ordenados por fecha"""
        future_events = Event.get_future_events()
        
        # Obtener los eventos en orden
        events_list = list(future_events)
        
        # Verificar que el primer evento es el actual (más cercano)
        self.assertEqual(events_list[0], self.current_event)
        
        # Verificar que el segundo evento es el futuro (más lejano)
        self.assertEqual(events_list[1], self.future_event)

    def test_event_is_past(self):
        """Test que verifica el método is_past() de Event"""
        # Verificar que el evento pasado es pasado
        self.assertTrue(self.past_event.is_past())
        
        # Verificar que el evento actual no es pasado
        self.assertFalse(self.current_event.is_past())
        
        # Verificar que el evento futuro no es pasado
        self.assertFalse(self.future_event.is_past()) 