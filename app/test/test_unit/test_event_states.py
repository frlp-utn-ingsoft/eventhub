from django.test import TestCase
from django.utils import timezone
import datetime

from app.models import Event, User, Venue, Category

class EventStatesUnitTest(TestCase):
    """Tests unitarios para la funcionalidad de estados de eventos"""

    def setUp(self):
        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador_states",
            email="organizador_states@example.com",
            password="password123",
            is_organizer=True,
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

        # Crear eventos con diferentes estados
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
            category=self.category
        )

    def test_event_initial_state(self):
        """Test que verifica que un evento nuevo tiene estado ACTIVE por defecto"""
        self.assertEqual(self.event.state, Event.ACTIVE)

    def test_event_canceled_state(self):
        """Test que verifica que se puede cancelar un evento"""
        self.event.state = Event.CANCELED
        self.event.save()
        self.assertEqual(self.event.state, Event.CANCELED)

    def test_event_reprogramed_state(self):
        """Test que verifica que se puede reprogramar un evento"""
        self.event.state = Event.REPROGRAMED
        self.event.save()
        self.assertEqual(self.event.state, Event.REPROGRAMED)

    def test_event_sold_out_state(self):
        """Test que verifica que se puede marcar un evento como agotado"""
        self.event.state = Event.SOLD_OUT
        self.event.save()
        self.assertEqual(self.event.state, Event.SOLD_OUT)

    def test_event_finished_state(self):
        """Test que verifica que se puede marcar un evento como finalizado"""
        self.event.state = Event.FINISHED
        self.event.save()
        self.assertEqual(self.event.state, Event.FINISHED)

    def test_auto_update_state_to_finished(self):
        """Test que verifica que un evento se marca como finalizado automáticamente cuando pasa su fecha"""
        # Crear un evento con fecha pasada
        past_event = Event.objects.create(
            title="Evento pasado",
            description="Descripción del evento pasado",
            scheduled_at=timezone.now() - datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
            category=self.category
        )
        
        # Llamar al método de actualización automática
        past_event.auto_update_state()
        
        # Verificar que el estado cambió a FINISHED
        self.assertEqual(past_event.state, Event.FINISHED)

    def test_auto_update_state_to_sold_out(self):
        """Test que verifica que un evento se marca como agotado automáticamente cuando no hay tickets disponibles"""
        # Crear un evento con capacidad 0
        self.venue.capacity = 0
        self.venue.save()
        
        # Llamar al método de actualización automática
        self.event.auto_update_state()
        
        # Verificar que el estado cambió a SOLD_OUT
        self.assertEqual(self.event.state, Event.SOLD_OUT)

    def test_update_method_sets_reprogramed_state(self):
        """Test que verifica que el método update cambia el estado a REPROGRAMED cuando se modifica la fecha"""
        # Guardar la fecha original
        original_date = self.event.scheduled_at
        
        # Actualizar con una nueva fecha
        new_date = timezone.now() + datetime.timedelta(days=2)
        self.event.update(scheduled_at=new_date)
        
        # Verificar que el estado cambió a REPROGRAMED
        self.assertEqual(self.event.state, Event.REPROGRAMED)
        self.assertNotEqual(self.event.scheduled_at, original_date) 