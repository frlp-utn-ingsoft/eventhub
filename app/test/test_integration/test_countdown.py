from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from app.models import User, Event, Location


User = get_user_model()

class CountdownViewTest(TestCase):
    def setUp(self):

        self.organizer_user = User.objects.create_user(
            username='organizer',
            password='testpass123',
            is_organizer=True,
        )

        self.normal_user = User.objects.create_user(
            username='normaluser',
            password='testpass123',
            is_organizer=False,
        )

        self.location = Location.objects.create(
            name='Lugar de prueba',
            address='Calle falsa 123',
            city='Ciudad',
            capacity=100,
            contact='contacto@prueba.com',
        )

        self.event = Event.objects.create(
            title='Evento de prueba',
            description='Descripción del evento',
            scheduled_at='2025-05-27 17:13:00',
            location=self.location,
            organizer=self.organizer_user,
        )

    def test_countdown_visible_to_non_organizer(self):
        self.client.login(username='normaluser', password='testpass123')
        url = reverse('event_detail', kwargs={'id': self.event.pk})
        response = self.client.get(url)
        self.assertContains(response, "countdown")

    def test_countdown_hidden_to_organizer(self):
        self.client.login(username='organizer', password='testpass123')
        url = reverse('event_detail', kwargs={'id': self.event.pk})
        response = self.client.get(url)
        self.assertNotContains(response, "countdown")
