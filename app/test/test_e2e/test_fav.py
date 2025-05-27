from app.models import Event, User
from app.test.test_e2e.base import BaseE2ETest 
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class FavoriteEventE2ETest(BaseE2ETest):

    def setUp(self):
        super().setUp()
        self.user = self.create_test_user()
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento",
            scheduled_at=timezone.now() + timedelta(days=1),
            organizer=self.user,
            price_general=Decimal('100.00'),
            price_vip=Decimal('200.00')
        )

    def test_user_can_favorite_event_from_list(self):
        self.login_user("usuario_test", "password123")

        self.page.goto(f"{self.live_server_url}/events/")

        # Confirmar que inicialmente el botón tiene ícono vacío
        favorite_btn = self.page.locator(f'a[href="/event/{self.event.id}/favorite/"]')
        assert favorite_btn.locator(".bi-heart").is_visible()

        # Click para marcar como favorito
        favorite_btn.click()

        # Verificar que el ícono cambió a lleno
        self.page.wait_for_selector(f'a[href="/event/{self.event.id}/favorite/"] .bi-heart-fill')
        assert favorite_btn.locator(".bi-heart-fill").is_visible()

    def test_user_can_view_favorites_list(self):
        self.login_user("usuario_test", "password123")

        self.user.favorite_events.add(self.event)

        self.page.goto(f"{self.live_server_url}/my_favorites/")

        # Verificar que el título del evento favorito aparece en la página
        assert self.page.locator(f"text=Evento de prueba").is_visible()

        # Verificar que el botón para quitar de favoritos está presente
        remove_fav_btn = self.page.locator(f'a[href="/event/{self.event.id}/favorite/"]')
        assert remove_fav_btn.is_visible()