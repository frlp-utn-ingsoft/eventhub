from django.test import TestCase
from django.utils import timezone
import datetime

from app.models import Event, User, Venue, Category

class EventFavoriteUnitTest(TestCase):
    """Tests unitarios para la funcionalidad de favoritos de eventos"""

    def setUp(self):
        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador_fav",
            email="organizador_fav@example.com",
            password="password123",
            is_organizer=True,
        )

        # Crear usuario regular
        self.regular_user = User.objects.create_user(
            username="usuario_fav",
            email="usuario_fav@example.com",
            password="password123",
            is_organizer=False,
        )

        # Crear venue y categoría
        self.venue = Venue.objects.create(
            name="Venue de prueba fav",
            adress="Dirección de prueba",
            city="Ciudad de prueba",
            capacity=100,
            contact="contacto@prueba.com"
        )

        self.category = Category.objects.create(
            name="Categoría de prueba fav",
            description="Descripción de la categoría de prueba",
            is_active=True
        )

        # Crear evento de prueba
        self.event = Event.objects.create(
            title="Evento de prueba fav",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
            category=self.category
        )

    def test_event_favorite_functionality(self):
        """Test que verifica la funcionalidad de marcar/desmarcar favoritos"""
        # Verificar que inicialmente no está en favoritos
        self.assertFalse(self.event.favorited_by.filter(id=self.regular_user.id).exists())

        # Agregar a favoritos
        self.event.favorited_by.add(self.regular_user)
        self.assertTrue(self.event.favorited_by.filter(id=self.regular_user.id).exists())

        # Quitar de favoritos
        self.event.favorited_by.remove(self.regular_user)
        self.assertFalse(self.event.favorited_by.filter(id=self.regular_user.id).exists()) 