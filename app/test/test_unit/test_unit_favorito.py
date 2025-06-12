from django.test import TestCase
from django.utils import timezone
from app.models import User, Event, Favorito

class FavoritoModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser')
        self.event = Event.objects.create(
            title="Evento Prueba",
            description="Descripción",
            scheduled_at=timezone.now() + timezone.timedelta(days=3),
            organizer=self.user
        )

    def test_favorito_creacion(self):
        favorito = Favorito.objects.create(usuario=self.user, evento=self.event)
        self.assertEqual(favorito.usuario, self.user)
        self.assertEqual(favorito.evento, self.event)
        self.assertTrue(Favorito.objects.filter(usuario=self.user, evento=self.event).exists())
