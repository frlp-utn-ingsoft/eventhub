# test_integration_notification.py

from django.test import TestCase
from django.urls import reverse
from app.models import User, Event, Ticket, Venue, Notification, Category
from datetime import timedelta
from django.utils import timezone


class NotificacionCambioEventoIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="integrationuser", 
            password="1234", 
            is_organizer=True
        )
        self.client.login(username="integrationuser", password="1234")
        
        self.venue = Venue.objects.create(
            name="Venue Test",
            address="Calle Falsa 123",
            city="Ciudad",
            capacity=100,
            contact_info="contacto@ejemplo.com",
            created_by=self.user
        )

        self.category = Category.objects.create(name="Test Category")

        self.event = Event.objects.create(
            title="Evento Integración",
            description="Test de notificación",
            scheduled_at=timezone.now() + timedelta(days=7),
            organizer=self.user,
            venue=self.venue,
            premium=False,
            status='activo'
        )
        self.event.categories.add(self.category)

        
        self.event.update_availability()

    
        self.ticket_buyer = User.objects.create_user(username="buyer", password="123")
        Ticket.objects.create(user=self.ticket_buyer, event=self.event, type="GENERAL", quantity=1, price_paid=100)
        self.event.refresh_from_db()


    def test_crea_notificacion_al_cambiar_fecha(self):
        nueva_fecha = self.event.scheduled_at + timedelta(days=3)

        
        response = self.client.post(reverse('event_edit', kwargs={'id': self.event.id}), {
            'title': self.event.title,
            'description': self.event.description,
            'scheduled_at': nueva_fecha.strftime('%Y-%m-%dT%H:%M'),
            'venue': self.venue.id,
            'categories': [self.category.id],
            'premium': False,
            'available_tickets': self.event.available_tickets,
            'status': 'activo',
        })
        
        self.assertEqual(response.status_code, 302, f"El formulario tuvo errores: {response.context.get('form').errors.as_json() if response.context else 'No form in context'}")

        notificaciones = Notification.objects.filter(user=self.ticket_buyer)
        self.assertEqual(notificaciones.count(), 1)
        self.assertIn("Fecha cambiada", notificaciones.first().message)

    def test_crea_notificacion_al_cambiar_lugar(self):
        nuevo_venue = Venue.objects.create(
            name="Nuevo Lugar",
            address="Otra calle 999",
            city="Otra ciudad",
            capacity=200,
            contact_info="nuevo@ejemplo.com",
            created_by=self.user
        )

        response = self.client.post(reverse('event_edit', kwargs={'id': self.event.id}), {
            'title': self.event.title,
            'description': self.event.description,
            'scheduled_at': self.event.scheduled_at.strftime('%Y-%m-%dT%H:%M'),
            'venue': nuevo_venue.id,
            'categories': [self.category.id],
            'premium': False,
            'available_tickets': self.event.available_tickets,
            'status': 'activo',
        })

        self.assertEqual(response.status_code, 302)

        notificaciones = Notification.objects.filter(user=self.ticket_buyer)
        self.assertEqual(notificaciones.count(), 1)
        self.assertIn("Lugar cambiado", notificaciones.first().message)
