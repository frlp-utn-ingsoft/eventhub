from django.test import TestCase
from app.models import User, Event, Venue
from django.utils import timezone
from datetime import timedelta


class CountdownFunctionalityTest(TestCase):
    """Tests unitarios para la funcionalidad de countdown de eventos"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_organizer=False  # Usuario NO organizador
        )
        
        self.organizer = User.objects.create_user(
            username='organizer',
            email='organizer@example.com',
            password='testpass123',
            is_organizer=True  # Usuario organizador
        )
        
        self.venue = Venue.objects.create(
            name='Test Venue',
            adress='Test Address',
            city='Test City',
            capacity=100,
            contact='test@venue.com'
        )

    def test_future_event_is_not_past(self):
        """Test que un evento futuro no está marcado como pasado"""
        future_event = Event.objects.create(
            title='Future Event',
            description='Test Description',
            scheduled_at=timezone.now() + timedelta(days=30),
            organizer=self.organizer,
            venue=self.venue
        )
        
        self.assertFalse(future_event.is_past())

    def test_past_event_is_past(self):
        """Test que un evento pasado está marcado como pasado"""
        past_event = Event.objects.create(
            title='Past Event',
            description='Test Description',
            scheduled_at=timezone.now() - timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue
        )
        
        self.assertTrue(past_event.is_past())

    def test_event_scheduled_at_is_timezone_aware(self):
        """Test que la fecha del evento es timezone-aware para JavaScript"""
        event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            scheduled_at=timezone.now() + timedelta(days=30),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Verificar que la fecha es timezone-aware
        self.assertIsNotNone(event.scheduled_at.tzinfo)
        
        # Verificar que es un objeto datetime válido
        self.assertIsInstance(event.scheduled_at, timezone.datetime)

    def test_get_future_events_for_countdown(self):
        """Test que get_future_events retorna solo eventos futuros para countdown"""
        # Crear evento futuro
        future_event = Event.objects.create(
            title='Future Event',
            description='Test Description',
            scheduled_at=timezone.now() + timedelta(days=30),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Crear evento pasado
        past_event = Event.objects.create(
            title='Past Event',
            description='Test Description',
            scheduled_at=timezone.now() - timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue
        )
        
        future_events = Event.get_future_events()
        
        # Solo el evento futuro debe aparecer
        self.assertIn(future_event, future_events)
        self.assertNotIn(past_event, future_events)

    def test_event_creation_for_countdown_display(self):
        """Test creación de evento con fecha futura para mostrar countdown"""
        future_date = timezone.now() + timedelta(days=15, hours=5, minutes=30)
        
        success, event = Event.new(
            title='Countdown Event',
            description='Event for testing countdown functionality',
            scheduled_at=future_date,
            organizer=self.organizer,
            venue=self.venue
        )
        
        self.assertTrue(success)
        self.assertIsInstance(event, Event)
        self.assertEqual(event.scheduled_at, future_date)
        self.assertFalse(event.is_past())

    def test_user_organizer_status_for_countdown_visibility(self):
        """Test que el estado de organizador se detecta correctamente"""
        # Usuario regular (debe ver countdown)
        self.assertFalse(self.user.is_organizer)
        
        # Usuario organizador (NO debe ver countdown)
        self.assertTrue(self.organizer.is_organizer)

    def test_event_organizer_relationship_for_countdown(self):
        """Test relación organizador-evento para lógica de countdown"""
        event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            scheduled_at=timezone.now() + timedelta(days=30),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # El organizador del evento debe ser el correcto
        self.assertEqual(event.organizer, self.organizer)
        
        # El usuario regular NO es organizador de este evento
        self.assertNotEqual(event.organizer, self.user)

    def test_countdown_time_calculation_logic(self):
        """Test lógica de cálculo de tiempo para countdown"""
        # Crear evento en exactamente 1 día, 2 horas, 30 minutos
        target_time = timezone.now() + timedelta(days=1, hours=2, minutes=30)
        
        event = Event.objects.create(
            title='Precise Time Event',
            description='Event for precise time testing',
            scheduled_at=target_time,
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Verificar que el evento no ha pasado
        self.assertFalse(event.is_past())
        
        # Verificar que la fecha programada es correcta
        self.assertEqual(event.scheduled_at, target_time)

    def test_event_validation_for_countdown(self):
        """Test validación de eventos para funcionalidad de countdown"""
        future_date = timezone.now() + timedelta(days=30)
        
        # Datos válidos
        errors = Event.validate(
            title='Valid Countdown Event',
            description='Valid description for countdown',
            scheduled_at=future_date
        )
        
        self.assertEqual(len(errors), 0)

    def test_event_validation_empty_fields(self):
        """Test validación con campos vacíos"""
        future_date = timezone.now() + timedelta(days=30)
        
        # Título vacío
        errors = Event.validate(
            title='',
            description='Valid description',
            scheduled_at=future_date
        )
        self.assertIn('title', errors)
        
        # Descripción vacía
        errors = Event.validate(
            title='Valid Title',
            description='',
            scheduled_at=future_date
        )
        self.assertIn('description', errors) 