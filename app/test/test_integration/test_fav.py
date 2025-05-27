from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from app.models import Event, User
from django.test import TestCase
from django.utils import timezone
import datetime
from decimal import Decimal


class ToggleFavoriteIntegrationTest(TestCase):
    def setUp(self):
        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            price_general=Decimal('100.00'),
            price_vip=Decimal('200.00')
        )
        self.client.login(username='organizador', password='password123')

    def test_user_can_favorite_event(self):
        # Hacer el request a la URL
        url = reverse('toggle_favorite', args=[self.event.id])
        response = self.client.get(url, follow=True)

        # Verificar que fue redirigido (HTTP 200 y no 302 final)
        self.assertEqual(response.status_code, 200)

        # Verificar que el evento fue agregado a favoritos del usuario
        self.assertIn(self.event, self.organizer.favorite_events.all())

        # Verificar que el mensaje aparece en la página redirigida
        self.assertContains(response, 'Eventos')


class MyFavoritesViewTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            price_general=Decimal('100.00'),
            price_vip=Decimal('200.00')
        )
        self.client.login(username='organizador', password='password123')
        self.organizer.favorite_events.add(self.event)

    def test_my_favorites_displays_user_favorites(self):
        response = self.client.get(reverse('my_favorites'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.title)
