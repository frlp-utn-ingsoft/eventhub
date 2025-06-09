import datetime
import re

from django.utils import timezone
from playwright.sync_api import expect

from app.models import Event, User, Venue, Category

from app.test.test_e2e.base import BaseE2ETest


class EventBaseTest(BaseE2ETest):
    """Clase base específica para tests de eventos"""

    def setUp(self):
        super().setUp()
        
        # Limpiar la base de datos antes de cada test
        Event.objects.all().delete()
        User.objects.all().delete()
        Venue.objects.all().delete()
        Category.objects.all().delete()

        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )

        # Crear usuario regular
        self.regular_user = User.objects.create_user(
            username="usuario",
            email="usuario@example.com",
            password="password123",
            is_organizer=False,
        )

        # Crear venue para los eventos
        self.venue = Venue.objects.create(
            name="Test Venue",
            adress="Test Address",
            city="Test City",
            capacity=100,
            contact="test@test.com"
        )

        # Crear categoría para los eventos
        self.category = Category.objects.create(
            name="Test Category",
            description="Test Description",
            is_active=True
        )

        # Crear eventos de prueba con fechas futuras
        current_time = timezone.now()
        # Evento 1 - 1 día en el futuro
        event_date1 = current_time + datetime.timedelta(days=1)
        self.event1 = Event.objects.create(
            title="Evento de prueba 1",
            description="Descripción del evento 1",
            scheduled_at=event_date1,
            organizer=self.organizer,
            venue=self.venue,
            category=self.category
        )

        # Evento 2 - 2 días en el futuro
        event_date2 = current_time + datetime.timedelta(days=2)
        self.event2 = Event.objects.create(
            title="Evento de prueba 2",
            description="Descripción del evento 2",
            scheduled_at=event_date2,
            organizer=self.organizer,
            venue=self.venue,
            category=self.category
        )

    def tearDown(self):
        # Limpiar la base de datos después de cada test
        Event.objects.all().delete()
        User.objects.all().delete()
        Venue.objects.all().delete()
        Category.objects.all().delete()
        super().tearDown()

    def _table_has_event_info(self):
        """Método auxiliar para verificar que la tabla tiene la información correcta de eventos"""
        # Verificar encabezados de la tabla
        headers = self.page.locator("table thead th")
        expect(headers.nth(0)).to_have_text("Título")
        expect(headers.nth(1)).to_have_text("Descripción")
        expect(headers.nth(2)).to_have_text("Fecha")
        expect(headers.nth(3)).to_have_text("Estado")
        expect(headers.nth(4)).to_have_text("Acciones")

        # Verificar que los eventos aparecen en la tabla
        rows = self.page.locator("table tbody tr")
        expect(rows).to_have_count(2)

        # Verificar datos del primer evento
        row0 = rows.nth(0)
        expect(row0.locator("td").nth(0)).to_have_text("Evento de prueba 1")
        expect(row0.locator("td").nth(1)).to_have_text("Descripción del evento 1")
        expect(row0.locator("td").nth(3)).to_have_text("ACTIVO")

        # Verificar datos del segundo evento
        expect(rows.nth(1).locator("td").nth(0)).to_have_text("Evento de prueba 2")
        expect(rows.nth(1).locator("td").nth(1)).to_have_text("Descripción del evento 2")
        expect(rows.nth(1).locator("td").nth(3)).to_have_text("ACTIVO")

    def _table_has_correct_actions(self, user_type):
        """Método auxiliar para verificar que las acciones son correctas según el tipo de usuario"""
        row0 = self.page.locator("table tbody tr").nth(0)

        # Verificar botón de detalle
        detail_button = row0.locator("a[href*='/events/']").first
        expect(detail_button).to_be_visible()
        expect(detail_button).to_have_attribute("href", f"/events/{self.event1.id}/")

        if user_type == "organizador":
            # Verificar botón de editar
            edit_button = row0.locator("a[href*='/edit/']")
            expect(edit_button).to_be_visible()
            expect(edit_button).to_have_attribute("href", f"/events/{self.event1.id}/edit/")

            # Verificar botón de eliminar
            delete_button = row0.locator("form[action*='/delete/'] button")
            expect(delete_button).to_be_visible()
            expect(delete_button).to_have_attribute("type", "submit")
        else:
            # Verificar que no hay botones de editar o eliminar
            expect(row0.locator("a[href*='/edit/']")).to_have_count(0)
            expect(row0.locator("form[action*='/delete/']")).to_have_count(0)


class EventAuthenticationTest(EventBaseTest):
    """Tests relacionados con la autenticación y permisos de usuarios en eventos"""

    def test_events_page_requires_login(self):
        """Test que verifica que la página de eventos requiere inicio de sesión"""
        # Cerrar sesión si hay alguna activa
        self.context.clear_cookies()

        # Intentar ir a la página de eventos sin iniciar sesión
        self.page.goto(f"{self.live_server_url}/events/")

        # Verificar que redirige a la página de login
        expect(self.page).to_have_url(re.compile(r"/accounts/login/"))


class EventDisplayTest(EventBaseTest):
    """Tests relacionados con la visualización de la página de eventos"""

    def test_events_page_display_as_organizer(self):
        """Test que verifica la visualización correcta de la página de eventos para organizadores"""
        self.login_user("organizador", "password123")
        self.page.goto(f"{self.live_server_url}/events/")

        # Verificar el título de la página
        expect(self.page).to_have_title("Eventos")

        # Verificar que existe un encabezado con el texto "Eventos"
        header = self.page.locator("h1")
        expect(header).to_have_text("Eventos")
        expect(header).to_be_visible()

        # Verificar que existe una tabla
        table = self.page.locator("table")
        expect(table).to_be_visible()

        self._table_has_event_info()
        self._table_has_correct_actions("organizador")

    def test_events_page_regular_user(self):
        """Test que verifica la visualización de la página de eventos para un usuario regular"""
        # Iniciar sesión como usuario regular
        self.login_user("usuario", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        expect(self.page).to_have_title("Eventos")

        # Verificar que existe un encabezado con el texto "Eventos"
        header = self.page.locator("h1")
        expect(header).to_have_text("Eventos")
        expect(header).to_be_visible()

        # Verificar que existe una tabla
        table = self.page.locator("table")
        expect(table).to_be_visible()

        self._table_has_event_info()
        self._table_has_correct_actions("regular")

    def test_events_page_no_events(self):
        """Test que verifica el comportamiento cuando no hay eventos"""
        # Eliminar todos los eventos
        Event.objects.all().delete()

        self.login_user("organizador", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        # Verificar que existe un mensaje indicando que no hay eventos
        no_events_message = self.page.locator("text=No hay eventos disponibles")
        expect(no_events_message).to_be_visible()


class EventPermissionsTest(EventBaseTest):
    """Tests relacionados con los permisos de usuario para diferentes funcionalidades"""

    def test_buttons_visible_only_for_organizer(self):
        """Test que verifica que los botones de gestión solo son visibles para organizadores"""
        # Primero verificar como organizador
        self.login_user("organizador", "password123")
        self.page.goto(f"{self.live_server_url}/events/")

        # Verificar que existe el botón de crear
        create_button = self.page.get_by_role("link", name="Crear Evento")
        expect(create_button).to_be_visible()

        # Cerrar sesión
        self.page.get_by_role("button", name="Salir").click()

        # Iniciar sesión como usuario regular
        self.login_user("usuario", "password123")
        self.page.goto(f"{self.live_server_url}/events/")

        # Verificar que NO existe el botón de crear
        create_button = self.page.get_by_role("link", name="Crear Evento")
        expect(create_button).to_have_count(0)


class EventCRUDTest(EventBaseTest):
    """Tests relacionados con las operaciones CRUD (Crear, Leer, Actualizar, Eliminar) de eventos"""

    def test_create_new_event_organizer(self):
        """Test que verifica la funcionalidad de crear un nuevo evento para organizadores"""
        # Iniciar sesión como organizador
        self.login_user("organizador", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        # Hacer clic en el botón de crear evento
        self.page.get_by_role("link", name="Crear Evento").click()

        # Verificar que estamos en la página de creación de evento
        expect(self.page).to_have_url(f"{self.live_server_url}/events/create/")

        header = self.page.locator("h1")
        expect(header).to_have_text("Crear evento")
        expect(header).to_be_visible()

        # Completar el formulario
        self.page.get_by_label("Título del Evento").fill("Evento de prueba E2E")
        self.page.get_by_label("Descripción").fill("Descripción creada desde prueba E2E")
        
        # Fecha futura (3 días desde ahora)
        future_date = (timezone.now() + datetime.timedelta(days=3)).strftime("%Y-%m-%d")
        self.page.get_by_label("Fecha").fill(future_date)
        self.page.get_by_label("Hora").fill("16:45")
        self.page.get_by_label("Lugar").select_option(value=str(self.venue.id))
        self.page.get_by_label("Categoría").select_option(value=str(self.category.id))

        # Enviar el formulario
        self.page.get_by_role("button", name="Crear Evento").click()

        # Verificar que redirigió a la página de eventos
        expect(self.page).to_have_url(f"{self.live_server_url}/events/")

        # Verificar que el nuevo evento aparece en la tabla
        rows = self.page.locator("table tbody tr")
        expect(rows).to_have_count(3)

        # Verificar que el nuevo evento está al final de la tabla
        last_row = rows.last
        expect(last_row.locator("td").nth(0)).to_have_text("Evento de prueba E2E")
        expect(last_row.locator("td").nth(1)).to_have_text("Descripción creada desde prueba E2E")
        expect(last_row.locator("td").nth(3)).to_have_text("ACTIVO")

    def test_edit_event_organizer(self):
        """Test que verifica la funcionalidad de editar un evento para organizadores"""
        # Iniciar sesión como organizador
        self.login_user("organizador", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        # Hacer clic en el botón editar del primer evento
        edit_button = self.page.locator("a[href*='/edit/']").first
        expect(edit_button).to_be_visible()
        edit_button.click()

        # Verificar que estamos en la página de edición
        expect(self.page).to_have_url(f"{self.live_server_url}/events/{self.event1.id}/edit/")

        header = self.page.locator("h1")
        expect(header).to_have_text("Editar evento")
        expect(header).to_be_visible()

        # Verificar que el formulario está precargado con los datos del evento y luego los editamos
        title = self.page.get_by_label("Título del Evento")
        expect(title).to_have_value("Evento de prueba 1")
        title.fill("Titulo editado")

        description = self.page.get_by_label("Descripción")
        expect(description).to_have_value("Descripción del evento 1")
        description.fill("Descripcion Editada")

        # Fecha futura (4 días desde ahora)
        future_date = (timezone.now() + datetime.timedelta(days=4)).strftime("%Y-%m-%d")
        date = self.page.get_by_label("Fecha")
        date.fill(future_date)

        time = self.page.get_by_label("Hora")
        time.fill("03:00")

        venue = self.page.get_by_label("Lugar")
        expect(venue).to_have_value(str(self.venue.id))

        category = self.page.get_by_label("Categoría")
        expect(category).to_have_value(str(self.category.id))

        # Enviar el formulario
        self.page.get_by_role("button", name="Guardar Cambios").click()

        # Verificar que redirigió a la página de eventos
        expect(self.page).to_have_url(f"{self.live_server_url}/events/")

        # Esperar a que la tabla se actualice
        self.page.wait_for_selector("table tbody tr")

        # Verificar que el evento editado aparece en la tabla con los nuevos datos
        rows = self.page.locator("table tbody tr")
        edited_row = rows.filter(has_text="Titulo editado")
        expect(edited_row).to_have_count(1)
        
        # Verificar los datos del evento editado
        expect(edited_row.locator("td").nth(0)).to_have_text("Titulo editado")
        expect(edited_row.locator("td").nth(1)).to_have_text("Descripcion Editada")
        expect(edited_row.locator("td").nth(3)).to_have_text("REPROGRAMADO")

    def test_delete_event_organizer(self):
        """Test que verifica la funcionalidad de eliminar un evento para organizadores"""
        # Iniciar sesión como organizador
        self.login_user("organizador", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        # Contar eventos antes de eliminar
        initial_count = len(self.page.locator("table tbody tr").all())

        # Hacer clic en el botón eliminar del primer evento
        delete_button = self.page.locator("form[action*='/delete/'] button").first
        expect(delete_button).to_be_visible()
        delete_button.click()

        # Verificar que redirigió a la página de eventos
        expect(self.page).to_have_url(f"{self.live_server_url}/events/")

        # Verificar que ahora hay un evento menos
        rows = self.page.locator("table tbody tr")
        expect(rows).to_have_count(initial_count - 1)

        # Verificar que el evento eliminado ya no aparece en la tabla
        expect(self.page.locator("table tbody tr").filter(has_text="Evento de prueba 1")).to_have_count(0)