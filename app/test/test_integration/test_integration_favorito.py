from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from app.models import Event, Favorito

User = get_user_model()

class FavoritoTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="1234")
        self.event = Event.objects.create(
            title="Test Event",
            description="Evento de prueba",
            scheduled_at=timezone.now() + timezone.timedelta(days=5),
            organizer=self.user
        )

    def test_agregar_y_eliminar_favorito(self):
        # Agregar favorito manualmente
        favorito = Favorito.objects.create(usuario=self.user, evento=self.event)

        # Verificar que el favorito fue agregado
        self.assertTrue(Favorito.objects.filter(usuario=self.user, evento=self.event).exists())

        # Eliminar el favorito
        favorito.delete()

        # Verificar que fue eliminado
        self.assertFalse(Favorito.objects.filter(usuario=self.user, evento=self.event).exists())
