import datetime
from django.utils import timezone
from playwright.sync_api import expect

from app.models import Event, Rating
from app.test.test_e2e.base import BaseE2ETest


class EventRatingsBaseTest(BaseE2ETest):
    """Clase base específica para tests de ratings de eventos"""

    def setUp(self):
        super().setUp()

        # Usar los usuarios ya creados en BaseE2ETest
        self.user1 = self.regular_user
        self.user2 = self.create_test_user(is_organizer=False)

        # Crear evento de prueba usando el venue ya creado en BaseE2ETest
        event_date = timezone.make_aware(datetime.datetime(2025, 2, 10, 10, 10))
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento",
            scheduled_at=event_date,
            organizer=self.organizer,
            venue=self.venue,
        )

        # Crear ratings de prueba
        self.rating1 = Rating.objects.create(
            title="Buenazo me encantó",
            text="Que lindo haberme gastado el aguinaldo en este evento. Recomiendo.",
            rating=5,
            event=self.event,
            user=self.user1
        )
        
        self.rating2 = Rating.objects.create(
            title="Esto es una bosta.",
            text="Prefiero pelear mano a mano con Topuria antes que ir a este evento.",
            rating=1,
            event=self.event,
            user=self.user2
        )


class EventRatingsDisplayTest(EventRatingsBaseTest):
    """Tests relacionados con la visualización de ratings de eventos"""

    def test_organizer_can_see_event_ratings(self):
        """Test que verifica que el organizador puede ver los ratings de sus eventos"""
        # Iniciar sesión como organizador
        self.login_user("organizador", "password123")

        # Ir a la página de detalle del evento
        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/")

        # Verificar que se muestra el promedio de ratings
        rating_section = self.page.locator(".event-ratings")
        expect(rating_section).to_be_visible()
        
        # Verificar que el promedio es correcto (3.0 = (5+1)/2)
        average_rating = self.page.locator(".average-rating")
        expect(average_rating).to_have_text("3.0")

        # Verificar que se muestra la cantidad de ratings
        rating_count = self.page.locator(".rating-count")
        expect(rating_count).to_have_text("(2 calificaciones)")

    def test_organizer_can_see_no_ratings_message(self):
        """Test que verifica que se muestra un mensaje cuando no hay ratings"""
        # Eliminar todos los ratings para este test específico
        Rating.objects.filter(event=self.event).delete()
        
        # Iniciar sesión como organizador
        self.login_user("organizador", "password123")

        # Ir a la página de detalle del evento
        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/")

        # Verificar que se muestra el mensaje de no hay ratings
        no_ratings_message = self.page.locator(".no-ratings-message")
        expect(no_ratings_message).to_be_visible()
        expect(no_ratings_message).to_have_text("Este evento aún no tiene calificaciones")

    def test_regular_user_can_see_ratings(self):
        """Test que verifica que usuarios regulares pueden ver los ratings"""
        # Iniciar sesión como usuario regular (usuario)
        self.login_user("usuario", "password123")

        # Ir a la página de detalle del evento
        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/")

        # Esperar a que la sección de ratings esté visible
        rating_section = self.page.locator(".event-ratings")
        rating_section.wait_for(state="visible", timeout=5000)
        expect(rating_section).to_be_visible()
        
        # Verificar que el promedio es correcto (3.0 = (5+1)/2)
        average_rating = self.page.locator(".average-rating")
        expect(average_rating).to_have_text("3.0")

        # Verificar que se muestra la cantidad de ratings
        rating_count = self.page.locator(".rating-count")
        expect(rating_count).to_have_text("(2 calificaciones)")


class EventRatingsInteractionTest(EventRatingsBaseTest):
    """Tests relacionados con la interacción con ratings de eventos"""

    def test_organizer_cannot_rate_own_event(self):
        """Test que verifica que un organizador no puede calificar su propio evento"""
        # Iniciar sesión como organizador
        self.login_user("organizador", "password123")

        # Ir a la página de detalle del evento
        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/")

        # Verificar que el enlace de calificación no está visible
        rating_link = self.page.get_by_role("link", name="Calificar evento")
        expect(rating_link).not_to_be_visible()

        # Intentar acceder directamente a la URL de calificación
        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/ratings/create/")

        # Verificar que se muestra el mensaje de error
        error_message = self.page.get_by_text("Los organizadores no pueden calificar sus propios eventos.")
        expect(error_message.first).to_be_visible()

