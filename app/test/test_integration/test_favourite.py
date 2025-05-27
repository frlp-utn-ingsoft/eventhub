from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from app.models import Event, FavoriteEvent
from django.utils import timezone

User = get_user_model()

class ToggleFavoriteIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='user1', password='pass')

        # Crear el evento con el organizador obligatorio
        self.event = Event.objects.create(
            title='Event',
            description='Descripción de prueba',
            scheduled_at=timezone.now(),
            organizer=self.user
        )

    def test_user_can_add_event_to_favorites(self):
        self.client.login(username='user1', password='pass')
        response = self.client.post(reverse('toggle_favorite', args=[self.event.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(FavoriteEvent.objects.filter(user=self.user, event=self.event).exists())

    def test_user_can_remove_event_from_favorites(self):
        FavoriteEvent.objects.create(user=self.user, event=self.event)
        self.client.login(username='user1', password='pass')
        response = self.client.post(reverse('toggle_favorite', args=[self.event.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(FavoriteEvent.objects.filter(user=self.user, event=self.event).exists())
