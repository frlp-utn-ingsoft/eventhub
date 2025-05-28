import datetime
import re

from django.utils import timezone
from playwright.sync_api import expect
from app.models import Event, User, Venue, Category
from app.test.test_e2e.base import BaseE2ETest

def assert_input_value_equals(locator, expected_value: str):
    actual_value = locator.input_value().replace(",", ".")
    assert actual_value == expected_value, f"Expected '{expected_value}', got '{actual_value}'"


class EventBaseTest(BaseE2ETest):
    """Clase base específica para tests de eventos"""

    def setUp(self):
        super().setUp()

        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )

        self.regular_user = User.objects.create_user(
            username="usuario",
            email="usuario@example.com",
            password="password123",
            is_organizer=False,
        )

        self.venue= Venue.objects.create(
            name="Auditorio Nacional",
            address="60 y 124",
            capacity=5000,
            country="ARG",  
            city="La Plata"
        )

        self.category = Category.objects.create(name="Conferencia")

        self.venue2= Venue.objects.create(
            name="Aula Parodi",
            address="60 y 118",
            capacity=300,
            country="ARG",  
            city="La Plata"
        )

        self.category2 = Category.objects.create(name="Exposición")

        event_date1 = timezone.make_aware(datetime.datetime(2025, 2, 10, 10, 10))
        self.event1 = Event.objects.create(
            title="Evento de prueba 1",
            description="Descripción del evento 1",
            scheduled_at=event_date1,
            organizer=self.organizer,
            venue=self.venue,
            price=50.00
        )
        self.event1.categories.add(self.category) 

        event_date2 = timezone.make_aware(datetime.datetime(2025, 5, 15, 14, 30))
        self.event2 = Event.objects.create(
            title="Evento de prueba 2",
            description="Descripción del evento 2",
            scheduled_at=event_date2,
            organizer=self.organizer,
            venue=self.venue,
            price=100.00
        )
        self.event2.categories.add(self.category) 

    def _table_has_event_info(self):
        """Método auxiliar para verificar que la tabla tiene la información correcta de eventos"""
        # Verificar encabezados de la tabla
        headers = self.page.locator("table thead th")
        expect(headers.nth(0)).to_have_text("Título")
        expect(headers.nth(1)).to_have_text("Descripción")
        expect(headers.nth(2)).to_have_text("Fecha")
        expect(headers.nth(3)).to_have_text("Categorías")
        expect(headers.nth(4)).to_have_text("Precio")
        expect(headers.nth(5)).to_have_text("Acciones")

        # Verificar que los eventos aparecen en la tabla
        rows = self.page.locator("table tbody tr")
        expect(rows).to_have_count(2)

        # Verificar datos del primer evento
        row0 = rows.nth(0)
        expect(row0.locator("td").nth(0)).to_have_text("Evento de prueba 1")
        expect(row0.locator("td").nth(1)).to_have_text("Descripción del evento 1")
        expect(row0.locator("td").nth(2)).to_have_text("10 Feb 2025, 10:10")
        expect(row0.locator("td").nth(4)).to_have_text("$50,00")

        # Verificar datos del segundo evento
        expect(rows.nth(1).locator("td").nth(0)).to_have_text("Evento de prueba 2")
        expect(rows.nth(1).locator("td").nth(1)).to_have_text("Descripción del evento 2")
        expect(rows.nth(1).locator("td").nth(2)).to_have_text("15 May 2025, 14:30")
        expect(rows.nth(1).locator("td").nth(4)).to_have_text("$100,00")

    def _table_has_correct_actions(self, user_type):
        """Método auxiliar para verificar que las acciones son correctas según el tipo de usuario"""
        row0 = self.page.locator("table tbody tr").nth(0)

        detail_button = row0.get_by_role("link", name="Ver Detalle")
        edit_button = row0.get_by_role("link", name="Editar")
        delete_form = row0.locator("form")

        expect(detail_button).to_be_visible()
        expect(detail_button).to_have_attribute("href", f"/events/{self.event1.id}/")

        if user_type == "organizador":
            expect(edit_button).to_be_visible()
            expect(edit_button).to_have_attribute("href", f"/events/{self.event1.id}/edit/")

            expect(delete_form).to_have_attribute("action", f"/events/{self.event1.id}/delete/")
            expect(delete_form).to_have_attribute("method", "POST")

            delete_button = delete_form.get_by_role("button", name="Eliminar")
            expect(delete_button).to_be_visible()
        else:
            expect(edit_button).to_have_count(0)
            expect(delete_form).to_have_count(0)


class EventAuthenticationTest(EventBaseTest):
    """Tests relacionados con la autenticación y permisos de usuarios en eventos"""

    def test_events_page_requires_login(self):
        """Test que verifica que la página de eventos requiere inicio de sesión"""
        # Cerrar sesión si hay alguna activa
        self.context.clear_cookies()

        self.page.goto(f"{self.live_server_url}/events/")

        expect(self.page).to_have_url(re.compile(r"/accounts/login/"))


class EventDisplayTest(EventBaseTest):
    """Tests relacionados con la visualización de la página de eventos"""

    def test_events_page_display_as_organizer(self):
        """Test que verifica la visualización correcta de la página de eventos para organizadores"""
        self.login_user("organizador", "password123")
        self.page.goto(f"{self.live_server_url}/my_events/")

        expect(self.page).to_have_title("Mis Eventos")

        header = self.page.locator("h1")
        expect(header).to_have_text("Mis Eventos")
        expect(header).to_be_visible()

        table = self.page.locator("table")
        expect(table).to_be_visible()

        self._table_has_event_info()
        self._table_has_correct_actions("organizador")

    def test_events_page_regular_user(self):
        """Test que verifica la visualización de la página de eventos para un usuario regular"""

        self.login_user("usuario", "password123")

        self.page.goto(f"{self.live_server_url}/events/")

        expect(self.page).to_have_title("Eventos")

        header = self.page.locator("h1")
        expect(header).to_have_text("Eventos")
        expect(header).to_be_visible()

        table = self.page.locator("table")
        expect(table).to_be_visible()

        self._table_has_event_info()
        self._table_has_correct_actions("regular")

    def test_events_page_no_events(self):
        """Test que verifica el comportamiento cuando no hay eventos"""

        Event.objects.all().delete()

        self.login_user("organizador", "password123")

        self.page.goto(f"{self.live_server_url}/events/")

        no_events_message = self.page.locator("text=No hay eventos disponibles")
        expect(no_events_message).to_be_visible()


class EventPermissionsTest(EventBaseTest):
    """Tests relacionados con los permisos de usuario para diferentes funcionalidades"""

    def test_buttons_visible_only_for_organizer(self):
        """Test que verifica que los botones de gestión solo son visibles para organizadores"""
   
        self.login_user("organizador", "password123")
        self.page.goto(f"{self.live_server_url}/my_events/")

        create_button = self.page.get_by_role("link", name="Crear Evento")
        expect(create_button).to_be_visible()

        self.page.get_by_role("button", name="Salir").click()

        self.login_user("usuario", "password123")
        self.page.goto(f"{self.live_server_url}/events/")

        create_button = self.page.get_by_role("link", name="Crear Evento")
        expect(create_button).to_have_count(0)


class EventCRUDTest(EventBaseTest):
    """Tests relacionados con las operaciones CRUD (Crear, Leer, Actualizar, Eliminar) de eventos"""

    def test_create_new_event_organizer(self):
        """Test que verifica la funcionalidad de crear un nuevo evento para organizadores"""

        self.login_user("organizador", "password123")

        self.page.goto(f"{self.live_server_url}/events/")

        self.page.get_by_role("link", name="Crear Evento").click()

        expect(self.page).to_have_url(f"{self.live_server_url}/events/create/")

        header = self.page.locator("h1")
        expect(header).to_have_text("Crear evento")
        expect(header).to_be_visible()

        self.page.get_by_label("Título del Evento").fill("Evento de prueba E2E")
        self.page.get_by_label("Precio").fill("20.00")
        self.page.get_by_label("Descripción").fill("Descripción creada desde prueba E2E")
        self.page.get_by_label("Fecha").fill("2025-06-15")
        self.page.get_by_label("Hora").fill("16:45")
        self.page.get_by_label(self.category.name).check()
        self.page.get_by_label("Lugar").select_option(str(self.venue.pk))

        self.page.get_by_role("button", name="Crear Evento").click()

        last_event = Event.objects.latest("id")
        expect(self.page).to_have_url(re.compile(f"{self.live_server_url}/events/{last_event.pk}/"))

        # Verificar que ahora hay 3 eventos
        self.page.goto(f"{self.live_server_url}/events/")
        rows = self.page.locator("table tbody tr")
        expect(rows).to_have_count(3)

        row = self.page.locator("table tbody tr").last
        expect(row.locator("td").nth(0)).to_have_text("Evento de prueba E2E")
        expect(row.locator("td").nth(1)).to_have_text("Descripción creada desde prueba E2E")
        expect(row.locator("td").nth(2)).to_have_text("15 Jun 2025, 16:45")
        expect(row.locator("td").nth(3)).to_have_text(self.category.name)
        expect(row.locator("td").nth(4)).to_have_text("$20,00")

    def test_edit_event_organizer(self):
        """Test que verifica la funcionalidad de editar un evento para organizadores"""

        self.login_user("organizador", "password123")
        self.page.goto(f"{self.live_server_url}/my_events/")
        self.page.get_by_role("link", name="Editar").first.click()
        expect(self.page).to_have_url(f"{self.live_server_url}/events/{self.event1.pk}/edit/")

        header = self.page.locator("h1")
        expect(header).to_have_text("Editar evento")
        expect(header).to_be_visible()

        # Verificar que el formulario está precargado con los datos del evento y luego los editamos
        title = self.page.get_by_label("Título del Evento")
        expect(title).to_have_value("Evento de prueba 1")
        title.fill("Titulo editado")
        price = self.page.get_by_label("Precio")
        assert_input_value_equals(price, "50.00")
        price.fill("30.00")
        
        description = self.page.get_by_label("Descripción")
        expect(description).to_have_value("Descripción del evento 1")
        description.fill("Descripcion Editada")
        
        date = self.page.get_by_label("Fecha")
        expect(date).to_have_value("2025-02-10")
        date.fill("2025-04-20")

        time = self.page.get_by_label("Hora")
        expect(time).to_have_value("10:10")
        time.fill("03:00")

        category = self.page.get_by_label(self.category.name)
        expect(category).to_be_checked()
        self.page.get_by_label(self.category2.name).check()

        venue = self.page.get_by_label("Lugar")
        expect(venue).to_have_value(str(self.venue.pk))
        self.page.get_by_label("Lugar").select_option(str(self.venue2.pk))

        self.page.get_by_role("button", name="Guardar Cambios").click()
        expect(self.page).to_have_url(f"{self.live_server_url}/events/{self.event1.pk}/")

        expect(self.page.get_by_text("Titulo editado")).to_be_visible()
        expect(self.page.get_by_text("Descripcion Editada")).to_be_visible()
        expect(self.page.get_by_text("domingo, 20 de abril de 2025, 03:00")).to_be_visible()
        expect(self.page.get_by_text(self.category2.name)).to_be_visible()
        expect(self.page.get_by_text("$30,00")).to_be_visible()
        #expect(self.page.get_by_text(self.venue2.name)).to_be_visible()

    def test_delete_event_organizer(self):
        """Test que verifica la funcionalidad de eliminar un evento para organizadores"""

        self.login_user("organizador", "password123")

        self.page.goto(f"{self.live_server_url}/my_events/")

        initial_count = len(self.page.locator("table tbody tr").all())

        self.page.get_by_role("button", name="Eliminar").first.click()

        expect(self.page).to_have_url(f"{self.live_server_url}/events/")

        rows = self.page.locator("table tbody tr")
        expect(rows).to_have_count(initial_count - 1)

        expect(self.page.get_by_text("Evento de prueba 1")).to_have_count(0)