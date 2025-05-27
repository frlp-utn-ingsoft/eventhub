from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from app.models import Event, Rating, Venue
import datetime
from django.utils import timezone

User = get_user_model()

class EventDetailIntegrationTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username='organizer', password='pass')
        self.user = User.objects.create_user(username='user1', password='pass')

        self.venue = Venue.objects.create(
            name='Auditorio UTN',
            address='Av. Siempreviva 742',
            capacity=200
        )
        
        self.event1 = Event.objects.create(
            title='Concierto de prueba',
            description='Un evento de integración',
            scheduled_at=timezone.now() + datetime.timedelta(days=7),
            organizer=self.organizer,
            venue=self.venue
        )

        Rating.objects.create(
            evento=self.event1, usuario=self.user,
            titulo="Muy bueno", calificacion=4, texto="Me gustó mucho"
        )

        self.client = Client()

    def test_rating_avegare_visible_organizer(self):
        self.client.login(username='organizer', password='pass')
        response = self.client.get(reverse('event_detail', args=[self.event1.id]))

        self.assertEqual(response.status_code, 200)
        self.assertIn('rating_average', response.context)
        self.assertEqual(response.context['rating_average'], 4)
    
    def test_rating_avegare_no_visible_others(self):
        self.client.login(username='user1', password='pass')
        response = self.client.get(reverse('event_detail', args=[self.event1.id]))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['rating_average'])