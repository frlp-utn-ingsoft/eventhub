from django.test import TestCase
from django.utils import timezone
from app.models import Event, Venue, User, Notification, Category, Ticket
import datetime
from django.urls import reverse

class NotificationIntegrationTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username="organizer", password="pass",  is_organizer=True)
        self.oldVenue = Venue.objects.create(name="Lugar 1", capacity=100)
        self.newVenue = Venue.objects.create(name="Lugar 2", capacity=100)
        self.category = Category.objects.create(name="Cat", is_active=True)
        self.user = User.objects.create_user(username='att', password='pass')
        self.oldeSceduledAt = timezone.now() + datetime.timedelta(days=1)
        self.newScheduledAt = timezone.now() + datetime.timedelta(days=2)
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=self.oldeSceduledAt,
            organizer=self.organizer,
            venue=self.oldVenue,
            category=self.category,
        )
        
        # Crear tickets para los usuarios
        Ticket.objects.create(event=self.event, user=self.user, quantity=1, type="GENERAL")
        

    def test_notification_created_on_event_update(self):
        """Test de integración que verifica la creación de notificaciones y su asociación con usuarios"""
        #Login del organizador
        self.client.login(username='organizer', password='pass')
        #Realizamos la petición de actualización del evento
        response = self.client.post(
            reverse('event_edit', args=[self.event.id]),
            {
                'title': 'Evento actualizado',
                'description': 'Descripción actualizada',
                'date': self.newScheduledAt.strftime("%Y-%m-%d"),
                'time': self.newScheduledAt.strftime("%H:%M"),
                'venue': self.newVenue.id,
                'category': self.category.id,
            }
        )
        #Login del usuario
        self.client.login(username='att', password='pass')
        #Verificamos que se haya creado la notificación y el usuario con ticket fue notificado
        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.first() 
        self.assertIn(self.user, notification.users.all())