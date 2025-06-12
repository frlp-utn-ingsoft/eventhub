import datetime
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from app.models import Event, User, Venue, Ticket, Notification


class EventNotificationUnitTest(TestCase):
    def setUp(self):
        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador_test",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )
        
        # Crear usuario comprador
        self.buyer = User.objects.create_user(
            username="comprador_test",
            email="comprador@example.com",
            password="password123",
        )
        
        # Crear venue
        self.venue = Venue.objects.create(
            name="Test Venue",
            address="Test Address",
            city="Test City",
            capacity=100,
            contact_info="Test Info",
            created_by=self.organizer,
        )
        
        # Crear evento inicial
        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            scheduled_at=timezone.now() + datetime.timedelta(days=5),  
            organizer=self.organizer,
            venue=self.venue,
            available_tickets=self.venue.capacity
        )
        
        # Crear ticket para el comprador
        self.ticket = Ticket.objects.create(
            user=self.buyer,
            event=self.event,
            ticket_code="TEST-123",
            quantity=1,
            type=Ticket.GENERAL,
            price_paid=100.00
        )

    def test_notification_created_on_date_change(self):
        """Verifica que se crea notificación al cambiar la fecha del evento"""
        old_date = self.event.scheduled_at
        new_date = old_date + datetime.timedelta(days=2)  # Cambiamos la fecha 2 días después
        
        # Verificar que no hay notificaciones al inicio
        initial_notifications = Notification.objects.filter(event=self.event).count()
        self.assertEqual(initial_notifications, 0)
        
        # Cambiar la fecha del evento
        self.event.scheduled_at = new_date
        self.event.save()  # Esto debería disparar el signal pre_save
        
        # Verificar que se creó una notificación
        notifications = Notification.objects.filter(event=self.event)
        self.assertEqual(notifications.count(), 1)
        
        # Verificar los datos de la notificación
        notification = notifications.first()
        self.assertEqual(notification.user, self.buyer)
        self.assertEqual(notification.event, self.event)
        self.assertFalse(notification.read)
        self.assertIn("Fecha cambiada de", notification.message)
        self.assertIn(str(old_date), notification.message)
        self.assertIn(str(new_date), notification.message)

    def test_no_notification_on_irrelevant_change(self):
        """Verifica que NO se crea notificación al cambiar campos no relevantes"""
        initial_count = Notification.objects.count()
        
        # Cambiar un campo que no debería triggerear notificación
        self.event.title = "Nuevo título del evento"
        self.event.save()
        
        # Verificar que no se crearon notificaciones nuevas
        self.assertEqual(Notification.objects.count(), initial_count)

    def test_notification_for_multiple_buyers(self):
        """Verifica que se crean notificaciones para todos los compradores"""
        # Crear segundo comprador
        buyer2 = User.objects.create_user(
            username="comprador2_test",
            email="comprador2@example.com",
            password="password123",
        )
        
        # Crear ticket para el segundo comprador
        Ticket.objects.create(
            user=buyer2,
            event=self.event,
            ticket_code="TEST-456",
            quantity=1,
            type=Ticket.GENERAL,
            price_paid=100.00
        )
        
        # Cambiar la fecha del evento
        new_date = self.event.scheduled_at + datetime.timedelta(days=3)
        self.event.scheduled_at = new_date
        self.event.save()
        
        # Verificar que hay 2 notificaciones (una por cada comprador)
        notifications = Notification.objects.filter(event=self.event)
        self.assertEqual(notifications.count(), 2)
        
        # Verificar que cada comprador recibió su notificación
        users_notified = {n.user for n in notifications}
        self.assertIn(self.buyer, users_notified)
        self.assertIn(buyer2, users_notified)