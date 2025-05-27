import datetime

from django.test import TestCase
from django.utils import timezone

from app.models import Event, User


class EventStatusModelTests(TestCase):
    """
    Tests específicos para la lógica de estados del modelo Event

    """
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador_status_test",
            email="status@example.com",
            password="password123",
            is_organizer=True,
        )
        # Crear eventos con diferentes status
        self.active_event = Event.objects.create(
            title="Evento Activo",
            description="Descripción...",
            scheduled_at=timezone.now() + datetime.timedelta(days=10),
            organizer=self.organizer,
            status='activo'
        )
        self.cancelled_event = Event.objects.create(
            title="Evento Cancelado",
            description="Descripción...",
            scheduled_at=timezone.now() + datetime.timedelta(days=5),
            organizer=self.organizer,
            status='cancelado'
        )
        self.reprogrammed_event = Event.objects.create(
            title="Evento Reprogramado",
            description="Descripción...",
            scheduled_at=timezone.now() + datetime.timedelta(days=15),
            organizer=self.organizer,
            status='reprogramado'
        )
        self.sold_out_event = Event.objects.create(
            title="Evento Agotado",
            description="Descripción...",
            scheduled_at=timezone.now() + datetime.timedelta(days=7),
            organizer=self.organizer,
            status='agotado'
        )
        self.finished_event = Event.objects.create(
            title="Evento Finalizado",
            description="Descripción...",
            scheduled_at=timezone.now() - datetime.timedelta(days=1), # Fecha en el pasado
            organizer=self.organizer,
            status='finalizado'
        )

    def test_event_status_choices_defined(self):
        """Verifica que las opciones de estado del evento están correctamente definidas en el modelo."""
        self.assertIsInstance(Event.EVENT_STATUS_CHOICES, list)
        self.assertGreater(len(Event.EVENT_STATUS_CHOICES), 0)
        # Verifica que al menos un par de opciones conocidas esten presentes
        self.assertIn(('activo', 'Activo'), Event.EVENT_STATUS_CHOICES)
        self.assertIn(('cancelado', 'Cancelado'), Event.EVENT_STATUS_CHOICES)

    def test_event_default_status(self):
        """Verifica que un evento se crea con el estado por defecto 'activo' si no se especifica."""
        event = Event.objects.create(
            title="Evento con default status",
            description="...",
            scheduled_at=timezone.now() + datetime.timedelta(days=20),
            organizer=self.organizer
            
        )
        self.assertEqual(event.status, 'activo')

    def test_event_status_update(self):
        """Verifica que el estado de un evento puede ser actualizado."""
        self.assertEqual(self.active_event.status, 'activo')
        self.active_event.update(status='cancelado') # llamada al metodo update del modelo
        updated_event = Event.objects.get(pk=self.active_event.pk)
        self.assertEqual(updated_event.status, 'cancelado')

        self.reprogrammed_event.update(status='agotado')
        updated_event = Event.objects.get(pk=self.reprogrammed_event.pk)
        self.assertEqual(updated_event.status, 'agotado')

    def test_get_upcoming_events_excludes_cancelled_and_finished(self):
        """
        Verifica que get_upcoming_events excluye eventos 'cancelado', 'agotado' y 'finalizado'
        incluso si su fecha es futura o presente
        """
        upcoming_events = Event.get_upcoming_events()
        
        self.assertIn(self.active_event, upcoming_events)
        self.assertIn(self.reprogrammed_event, upcoming_events)
        
        self.assertNotIn(self.cancelled_event, upcoming_events)
        self.assertNotIn(self.sold_out_event, upcoming_events)
        self.assertNotIn(self.finished_event, upcoming_events) 
        
        # Verificar la cantidad de eventos esperados
        self.assertEqual(len(upcoming_events), 2) 
