import datetime
from django.test import TestCase
from app.models import User,Event, Rating
from django.utils import timezone
from django.urls import reverse

class RatingPromedioTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador_test",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )
        self.client.login(username="organizador_test", password="password123")
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
        )
        self.url = reverse('event_detail', args=[self.event.id])
        
    def test_promedio_no_visible_sin_calificaciones(self):
        response = self.client.get(self.url)
        

        self.assertContains(response, 'Calificación promedio')
        self.assertContains(response, 'Sin calificaciones')