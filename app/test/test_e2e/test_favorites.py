from django.utils import timezone
from playwright.sync_api import expect
import datetime

from app.models import Event, User, Venue, Category
from app.test.test_e2e.base import BaseE2ETest

class EventFavoriteE2ETest(BaseE2ETest):
    """Tests end-to-end para la funcionalidad de favoritos de eventos"""

    def setUp(self):
        super().setUp()

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

    def test_favorite_functionality(self):
        """Test e2e que verifica la funcionalidad completa de favoritos"""
        # Login como usuario regular
        self.page.goto(f"{self.live_server_url}/accounts/login/")
        self.page.fill('input[name="username"]', "usuario_fav")
        self.page.fill('input[name="password"]', "password123")
        self.page.click('button[type="submit"]')
        
        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")
        
        # Verificar que el botón de favorito está visible
        favorite_button = self.page.locator(f'[href="/events/{self.event.id}/toggle-favorite/"]')
        expect(favorite_button).to_be_visible()
        
        # Marcar el evento como favorito
        favorite_button.click()
        
        # Verificar que aparece el mensaje de éxito
        expect(self.page.locator('.alert-success')).to_contain_text("Evento agregado a favoritos")
        
        # Verificar que la estrella está llena
        expect(self.page.locator(f'[href="/events/{self.event.id}/toggle-favorite/"] i.bi-star-fill')).to_be_visible()
        
        # Quitar el evento de favoritos
        favorite_button.click()
        
        # Verificar que aparece el mensaje de éxito
        expect(self.page.locator('.alert-success')).to_contain_text("Evento removido de favoritos")
        
        # Verificar que la estrella está vacía
        expect(self.page.locator(f'[href="/events/{self.event.id}/toggle-favorite/"] i.bi-star')).to_be_visible() 