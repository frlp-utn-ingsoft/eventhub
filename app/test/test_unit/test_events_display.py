import datetime

from django.test import TestCase
from django.utils import timezone

from app.models import Category, Event, User


class EventDisplayModelTests(TestCase):
    """Tests para las funciones de recuperación de eventos del modelo Event."""
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador_test_display",
            email="organizador_display@example.com",
            password="password123",
            is_organizer=True,
        )

        cat = Category.objects.create(name="General")

        now = timezone.now()
        # Eventos pasados
        self.past_event_1 = Event.objects.create(
            title="Pasado 1", description="...", scheduled_at=now - datetime.timedelta(days=1), 
            organizer=self.organizer, status='finalizado' 
        )
        self.past_event_2 = Event.objects.create(
            title="Pasado 2", description="...", scheduled_at=now - datetime.timedelta(days=2), 
            organizer=self.organizer, status='finalizado' 
        )
        # Eventos futuros (activo por defecto)
        self.future_event_1 = Event.objects.create(
            title="Futuro 1", description="...", scheduled_at=now + datetime.timedelta(days=1), 
            organizer=self.organizer, status='activo' 
        )
        self.future_event_2 = Event.objects.create(
            title="Futuro 2", description="...", scheduled_at=now + datetime.timedelta(days=2), 
            organizer=self.organizer, status='activo' 
        )
        self.future_event_3 = Event.objects.create(
            title="Futuro 3", description="...", scheduled_at=now + datetime.timedelta(days=2), 
            organizer=self.organizer, status='reprogramado' 
        )
        # Evento futuro cancelado
        self.cancelled_future_event = Event.objects.create(
            title="Cancelado Futuro", description="...", scheduled_at=now + datetime.timedelta(days=5), 
            organizer=self.organizer, status='cancelado'
        )


        self.past_event_1.categories.add(cat)
        self.past_event_2.categories.add(cat)
        self.future_event_1.categories.add(cat)
        self.future_event_2.categories.add(cat)
        self.future_event_3.categories.add(cat)
        self.cancelled_future_event.categories.add(cat)
    
    def test_get_upcoming_events(self):
        """Verifica que get_upcoming_events solo trae eventos futuros 'activo' o 'reprogramado'."""
        qs = Event.get_upcoming_events()
       
        self.assertEqual(len(qs), 3) 
        self.assertIn(self.future_event_1, qs)
        self.assertIn(self.future_event_2, qs)
        self.assertIn(self.future_event_3, qs)
        self.assertNotIn(self.past_event_1, qs) # Evento pasado
        self.assertNotIn(self.past_event_2, qs) # Evento pasado
        self.assertNotIn(self.cancelled_future_event, qs) # Evento cancelado (no deberia aparecer)

    def test_get_all_events(self):
        """Verifica que get_all_events trae todos los eventos sin importar el status."""
        qs = Event.get_all_events()
        self.assertEqual(len(qs), 6) 
        self.assertIn(self.past_event_1, qs)
        self.assertIn(self.past_event_2, qs)
        self.assertIn(self.future_event_1, qs)
        self.assertIn(self.future_event_2, qs)
        self.assertIn(self.future_event_3, qs)
        self.assertIn(self.cancelled_future_event, qs) 