from django.test import TestCase
from django.contrib.auth import get_user_model
from app.models import Event, FavoriteEvent
from django.utils import timezone

User = get_user_model()

class FavoriteEventModelTest(TestCase):
    def test_create_favorite_event(self):
        # Crear un usuario de prueba
        user = User.objects.create_user(username='testuser', password='12345')

        # Crear un evento con el usuario como organizador
        event = Event.objects.create(
            title='Evento Test',
            description='Este es un evento de prueba.',
            scheduled_at=timezone.now(),
            organizer=user
        )

        # Crear un favorito (evento favorito)
        fav = FavoriteEvent.objects.create(user=user, event=event)

        # Validar que el favorito se creó correctamente
        self.assertEqual(fav.user, user)
        self.assertEqual(fav.event, event)
        self.assertTrue(FavoriteEvent.objects.filter(user=user, event=event).exists())
