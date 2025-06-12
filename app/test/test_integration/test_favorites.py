from django.test import TestCase, Client
from django.utils import timezone
from app.models import Event, User, Venue, Category
import datetime

class EventFavoriteIntegrationTest(TestCase):
    """Tests de integración para la funcionalidad de favoritos de eventos"""

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

        # Cliente para hacer peticiones
        self.client = Client()

    def test_toggle_favorite_view(self):
        """Test que verifica la vista de toggle_favorite"""
        # Login como usuario regular
        self.client.login(username="usuario_fav", password="password123")
        
        # Intentar marcar un evento como favorito
        response = self.client.get(f'/events/{self.event.id}/toggle-favorite/')
        self.assertEqual(response.status_code, 302)  # Redirección
        
        # Verificar que el evento fue agregado a favoritos
        self.assertTrue(self.event.favorited_by.filter(id=self.regular_user.id).exists())
        
        # Intentar quitar el evento de favoritos
        response = self.client.get(f'/events/{self.event.id}/toggle-favorite/')
        self.assertEqual(response.status_code, 302)  # Redirección
        
        # Verificar que el evento fue quitado de favoritos
        self.assertFalse(self.event.favorited_by.filter(id=self.regular_user.id).exists())

    def test_favorite_button_not_visible_for_organizer(self):
        """Test que verifica que el botón de favorito no es visible para organizadores"""
        # Login como organizador
        self.client.login(username="organizador_fav", password="password123")
        
        # Obtener la página de eventos
        response = self.client.get('/events/')
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el botón de favorito no está en la respuesta
        self.assertNotContains(response, 'toggle-favorite') 