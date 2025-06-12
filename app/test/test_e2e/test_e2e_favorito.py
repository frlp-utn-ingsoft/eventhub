import datetime
from django.utils import timezone
from playwright.sync_api import expect
from app.models import Event, User
from app.test.test_e2e.base import BaseE2ETest


class FavoriteBaseTest(BaseE2ETest):
    """Clase base para tests de favoritos"""

    def setUp(self):
        super().setUp()

        # Crear usuario
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="1234",
        )

        # Crear evento
        self.event = Event.objects.create(
            title="Evento Django",
            description="Charlas sobre Django y más",
            scheduled_at=timezone.now() + datetime.timedelta(days=3),
            organizer=self.user,
        )


class FavoriteFunctionalityTest(FavoriteBaseTest):
    """Tests funcionales de favoritos"""

    def test_user_can_add_and_remove_favorite(self):
        """Verifica que el usuario pueda agregar y eliminar un evento de favoritos"""
        self.login_user("testuser", "1234")

        # Ir al detalle del evento
        self.page.goto(f"{self.live_server_url}/events/")

        add_button = self.page.locator('a[title="Añadir a favoritos"]')
        
        # Esperar hasta que el botón esté visible o fallar con mensaje útil
        try:
            add_button.wait_for(state="visible", timeout=10000)
        except Exception:
            print("ERROR: El botón 'Añadir a favoritos' no apareció en la página.")
            print("Contenido HTML de la página para depuración:")
            print(self.page.content())
            raise
        
        expect(add_button).to_be_visible()

        # Hacer clic para agregar a favoritos
        add_button.click()

        remove_button = self.page.locator('a[title="Quitar de favoritos"]')
        remove_button.wait_for(state="visible", timeout=10000)
        expect(remove_button).to_be_visible()

        # Hacer clic para quitar de favoritos
        remove_button.click()

        # Esperar que vuelva el botón "Añadir a favoritos"
        add_button = self.page.locator('a[title="Añadir a favoritos"]')
        add_button.wait_for(state="visible", timeout=10000)
        expect(add_button).to_be_visible()
