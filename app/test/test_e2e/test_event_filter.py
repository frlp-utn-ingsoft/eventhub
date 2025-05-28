# app/test/test_e2e/test_event_filter.py

from django.utils import timezone
import datetime
from playwright.sync_api import expect

from app.models import Event, User, Venue, Category
from app.test.test_e2e.base import BaseE2ETest

class EventFilterE2ETest(BaseE2ETest):
    """Tests end-to-end para la funcionalidad de filtrado de eventos"""

    def setUp(self):
        super().setUp()
        # Limpiar TODOS los eventos al inicio de cada test para asegurar un estado limpio
        Event.objects.all().delete()
        # Ya no creamos los 3 eventos aquí.

    def _create_standard_events(self):
        """Método auxiliar para crear el conjunto estándar de eventos (pasado, actual, futuro)"""
        # Evento pasado
        past_date = timezone.now() - datetime.timedelta(days=1)
        self.past_event = Event.objects.create(
            title="Evento pasado",
            description="Descripción del evento pasado",
            scheduled_at=past_date,
            organizer=self.organizer,
            venue=self.venue,
            category=self.category
        )

        # Evento actual (muy cercano al "ahora" o en la próxima hora, debería aparecer)
        current_date = timezone.now() + datetime.timedelta(minutes=5)
        self.current_event = Event.objects.create(
            title="Evento actual",
            description="Descripción del evento actual",
            scheduled_at=current_date,
            organizer=self.organizer,
            venue=self.venue,
            category=self.category
        )

        # Evento futuro (más lejano)
        future_date = timezone.now() + datetime.timedelta(days=1)
        self.future_event = Event.objects.create(
            title="Evento futuro",
            description="Descripción del evento futuro",
            scheduled_at=future_date,
            organizer=self.organizer,
            venue=self.venue,
            category=self.category
        )

    def test_events_page_shows_only_future_events(self):
        """Test que verifica que la página de eventos solo muestra eventos futuros"""
        self._create_standard_events() # Crea los eventos necesarios para este test

        # Iniciar sesión como usuario regular
        self.login_user("usuario", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")
        self.page.wait_for_load_state("networkidle")

        # Esperar a que la tabla esté visible
        table = self.page.locator("table")
        expect(table).to_be_visible()

        # Verificar que solo se muestran los eventos futuros
        event_titles_locators = self.page.locator("table tbody tr")
        expect(event_titles_locators).to_have_count(2, timeout=10000)  # Esperar 2 eventos (futuro y actual)

        # Obtener los textos de los títulos visibles
        event_titles_text = [row.locator("td").first.inner_text() for row in event_titles_locators.all()]
        
        self.assertNotIn("Evento pasado", event_titles_text)
        self.assertIn("Evento futuro", event_titles_text)
        self.assertIn("Evento actual", event_titles_text)

    def test_events_are_ordered_by_date(self):
        """Test que verifica que los eventos están ordenados por fecha"""
        self._create_standard_events() # Crea los eventos necesarios para este test

        # Iniciar sesión como usuario regular
        self.login_user("usuario", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")
        self.page.wait_for_load_state("networkidle")

        # Esperar a que la tabla esté visible
        table = self.page.locator("table")
        expect(table).to_be_visible()

        # Obtener los eventos en orden
        event_titles = self.page.locator("table tbody tr")
        
        # Verificar que el primer evento es el actual (más cercano)
        first_event_title = event_titles.nth(0).locator("td").first
        expect(first_event_title).to_be_visible()
        expect(first_event_title).to_have_text("Evento actual")
        
        # Verificar que el segundo evento es el futuro (más lejano)
        second_event_title = event_titles.nth(1).locator("td").first
        expect(second_event_title).to_be_visible()
        expect(second_event_title).to_have_text("Evento futuro")

    def test_no_events_message(self):
        """Test que verifica que se muestra el mensaje correcto cuando no hay eventos futuros"""
        # En este test, los eventos ya han sido eliminados por el setUp() de la clase,
        # así que la base de datos de eventos está vacía.

        # Iniciar sesión como usuario regular
        self.login_user("usuario", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")
        self.page.wait_for_load_state("networkidle")

        # Esperar a que la tabla esté visible
        table = self.page.locator("table")
        expect(table).to_be_visible()

        # Verificar que se muestra el mensaje de no hay eventos
        no_events_message = self.page.locator("text=No hay eventos disponibles")
        expect(no_events_message).to_be_visible()

        # MODIFICACIÓN CLAVE AQUÍ:
        # En lugar de esperar 0 filas de 'tr', esperamos 1 fila que CONTENGA el mensaje.
        # O, si no quieres contar esa fila, puedes contar las filas que representan datos reales
        # Si la fila de "No hay eventos" es la única en <tbody>, esta es la mejor opción:
        expect(self.page.locator("table tbody tr")).to_have_count(1, timeout=10000)
        expect(self.page.locator("table tbody tr:has-text('No hay eventos disponibles')")).to_be_visible()
        
        # Si prefieres asegurarte de que NO haya filas que *no* sean el mensaje:
        # Puedes usar un selector negativo si sabes qué distingue a las filas de eventos reales.
        # Por ejemplo, si los eventos reales tienen un botón, o una clase 'event-item':
        # expect(self.page.locator("table tbody tr:not(:has-text('No hay eventos disponibles'))")).to_have_count(0, timeout=10000)