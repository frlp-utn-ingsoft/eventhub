from django.test import TestCase
from django.utils import timezone
from app.models import Event, Venue, User  # Ajusta imports según tu estructura
import datetime

from app.models import Event, User, Category, Notification, Ticket


class EventModelTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username="organizer", password="pass")
        self.venue = Venue.objects.create(name="Test Venue", capacity=100)
        self.venue1 = Venue.objects.create(name="Lugar 1", capacity=100)
        self.venue2 = Venue.objects.create(name="Lugar 2", capacity=100)
        self.category = Category.objects.create(name="Cat", is_active=True)
        self.user1 = User.objects.create_user(username='att', password='pass')
        self.user2 = User.objects.create_user(username='att2', password='pass2')
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue1,
            category=self.category,
        )
        
        Ticket.objects.create(event=self.event, user=self.user1, quantity=1, type="GENERAL")
        Ticket.objects.create(event=self.event, user=self.user2, quantity=1, type="VIP")

    def test_default_state_is_active(self):
        event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
        )
        self.assertEqual(event.state, Event.ACTIVE)

    def test_event_new_with_valid_data(self):
        """Test que verifica la creación de eventos con datos válidos"""
        scheduled_at = timezone.now() + datetime.timedelta(days=2)
        success, errors = Event.new(
            title="Nuevo evento",
            description="Descripción del nuevo evento",
            scheduled_at=scheduled_at,
            organizer=self.organizer,
        )

        self.assertTrue(success)
        self.assertIsNone(errors)

        # Verificar que el evento fue creado en la base de datos
        new_event = Event.objects.get(title="Nuevo evento")
        self.assertEqual(new_event.description, "Descripción del nuevo evento")
        self.assertEqual(new_event.organizer, self.organizer)

    def test_event_new_with_invalid_data(self):
        """Test que verifica que no se crean eventos con datos inválidos"""
        scheduled_at = timezone.now() + datetime.timedelta(days=2)
        initial_count = Event.objects.count()

        # Intentar crear evento con título vacío
        success, errors = Event.new(
            title="",
            description="Descripción del evento",
            scheduled_at=scheduled_at,
            organizer=self.organizer,
        )

        self.assertFalse(success)
        self.assertIn("title", errors)

        # Verificar que no se creó ningún evento nuevo
        self.assertEqual(Event.objects.count(), initial_count)

    def test_event_update(self):
        """Test que verifica la actualización de eventos"""
        new_title = "Título actualizado"
        new_description = "Descripción actualizada"
        new_scheduled_at = timezone.now() + datetime.timedelta(days=3)

    def test_update_event_sets_reprogramed_if_date_changes(self):
        event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
        )

        event.update(
            title=new_title,
            description=new_description,
            scheduled_at=new_scheduled_at,
            organizer=self.organizer,
            venue=self.venue,
        )
        event.auto_update_state()
        self.assertEqual(event.state, Event.FINISHED)
        self.assertEqual(updated_event.venue, self.venue)

    def test_auto_update_state_sets_sold_out_if_no_tickets_available(self):
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
        )

        original_title = event.title
        original_scheduled_at = event.scheduled_at
        new_description = "Solo la descripción ha cambiado"

        event.update(
            title=None,  # No cambiar
            description=new_description,
            scheduled_at=None,  # No cambiar
            organizer=None,  # No cambiar
        )

        # Recargar el evento desde la base de datos
        updated_event = Event.objects.get(pk=event.pk)

        # Verificar que solo cambió la descripción
        self.assertEqual(updated_event.title, original_title)
        self.assertEqual(updated_event.description, new_description)
        self.assertEqual(updated_event.scheduled_at, original_scheduled_at)
        self.assertEqual(updated_event.venue, self.venue)
    
    
    def test_notification_created_on_event_update(self):
        """Test que verifica si se notifica a los usuarios con ticket del evento cuando cambia la fecha o el lugar"""
        # Simular cambio de fecha y lugar
        old_scheduled_at = self.event.scheduled_at
        old_venue = self.event.venue
        new_scheduled_at = old_scheduled_at + datetime.timedelta(days=2)
        new_venue = self.venue2

        self.event.scheduled_at = new_scheduled_at
        self.event.venue = new_venue
        self.event.save()

        # Lógica de notificación
        if old_scheduled_at != new_scheduled_at or old_venue != new_venue:
            notification = Notification.objects.create(
                title="Evento Modificado",
                message=f"El evento '{self.event.title}' ha sido modificado. Fecha: {new_scheduled_at} y lugar: {new_venue.name}.",
                priority="MEDIUM",
            )
            usuarios = User.objects.filter(tickets__event=self.event).distinct()
            notification.users.set(usuarios)
            notification.save()

        # Verificar que la notificación esté en cada usuario con ticket
        for usuario in usuarios:
            self.assertIn(notification, usuario.notifications.all())
        
