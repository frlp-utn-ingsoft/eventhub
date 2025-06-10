import datetime
import re
from datetime import timedelta

from django.utils import timezone
from playwright.sync_api import expect
import pytz

from app.models import Event, User

from app.test.test_e2e.base import BaseE2ETest


class EventBaseTest(BaseE2ETest):
    """Clase base específica para tests de eventos"""

    def setUp(self):
        super().setUp()

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

        # Crear eventos de prueba usando fechas relativas a now()
        now = timezone.now()
        
        # Evento 1 (futuro, 1 mes adelante)
        event_date1 = now + timedelta(days=30)
        self.event1 = Event.objects.create(
            title="Evento de prueba 1",
            description="Descripción del evento 1",
            scheduled_at=event_date1,
            organizer=self.organizer,
        )

        # Evento 2 (futuro, 2 meses adelante)
        event_date2 = now + timedelta(days=60)
        self.event2 = Event.objects.create(
            title="Evento de prueba 2",
            description="Descripción del evento 2",
            scheduled_at=event_date2,
            organizer=self.organizer,
        )

        # Evento 3 (pasado, 1 día atrás)
        event_date3 = now - timedelta(days=1)
        self.event3 = Event.objects.create(
            title="Evento pasado",
            description="Descripción del evento pasado",
            scheduled_at=event_date3,
            organizer=self.organizer,
        )

    def tearDown(self):
        timezone.deactivate()
        super().tearDown()

    def _table_has_event_info(self, show_past=False):
        """Método auxiliar para verificar que la tabla tiene la información correcta de eventos"""
        # Esperar a que la tabla esté visible
        table = self.page.locator("table")
        expect(table).to_be_visible()

        # Verificar encabezados de la tabla
        header_texts = self.page.locator("table thead th").all_inner_texts()
        assert "Título" in header_texts
        assert "Descripción" in header_texts
        assert "Fecha" in header_texts
        assert "Acciones" in header_texts

        # Esperar a que los eventos estén cargados
        self.page.wait_for_selector("table tbody tr")

        # Verificar que los eventos aparecen en la tabla
        rows = self.page.locator("table tbody tr")
        expected_count = 3 if show_past else 2
        expect(rows).to_have_count(expected_count)

        if show_past:
            # Cuando show_past=True, los eventos están ordenados por fecha descendente
            # Evento 2 (más reciente)
            row0 = rows.nth(0)
            expect(row0.locator("td").nth(0)).to_have_text("Evento de prueba 2")
            expect(row0.locator("td").nth(1)).to_have_text("Descripción del evento 2")
            date_text = row0.locator("td").nth(2).inner_text()
            assert re.match(r"\d{1,2} [a-z]{3} \d{4}, \d{2}:\d{2}", date_text)

            # Evento 1
            row1 = rows.nth(1)
            expect(row1.locator("td").nth(0)).to_have_text("Evento de prueba 1")
            expect(row1.locator("td").nth(1)).to_have_text("Descripción del evento 1")
            date_text = row1.locator("td").nth(2).inner_text()
            assert re.match(r"\d{1,2} [a-z]{3} \d{4}, \d{2}:\d{2}", date_text)

            # Evento pasado
            past_event_row = rows.nth(2)
            expect(past_event_row.locator("td").nth(0)).to_have_text("Evento pasado")
            expect(past_event_row.locator("td").nth(1)).to_have_text("Descripción del evento pasado")
            date_text = past_event_row.locator("td").nth(2).inner_text()
            assert re.match(r"\d{1,2} [a-z]{3} \d{4}, \d{2}:\d{2}", date_text)
        else:
            # Cuando show_past=False, solo se muestran eventos futuros ordenados por fecha ascendente
            # Evento 1 (más próximo)
            row0 = rows.nth(0)
            expect(row0.locator("td").nth(0)).to_have_text("Evento de prueba 1")
            expect(row0.locator("td").nth(1)).to_have_text("Descripción del evento 1")
            date_text = row0.locator("td").nth(2).inner_text()
            assert re.match(r"\d{1,2} [a-z]{3} \d{4}, \d{2}:\d{2}", date_text)

            # Evento 2
            row1 = rows.nth(1)
            expect(row1.locator("td").nth(0)).to_have_text("Evento de prueba 2")
            expect(row1.locator("td").nth(1)).to_have_text("Descripción del evento 2")
            date_text = row1.locator("td").nth(2).inner_text()
            assert re.match(r"\d{1,2} [a-z]{3} \d{4}, \d{2}:\d{2}", date_text)

    def _table_has_correct_actions(self, user_type, show_past=False):
        """Método auxiliar para verificar que las acciones son correctas según el tipo de usuario"""
        # Esperar a que la tabla esté visible
        table = self.page.locator("table")
        expect(table).to_be_visible()

        # Esperar a que los eventos estén cargados
        self.page.wait_for_selector("table tbody tr")

        # Obtener la primera fila según el orden de los eventos
        if show_past:
            # Cuando show_past=True, el evento 2 aparece primero
            row0 = self.page.locator("table tbody tr").nth(0)
            event = self.event2
        else:
            # Cuando show_past=False, el evento 1 aparece primero
            row0 = self.page.locator("table tbody tr").nth(0)
            event = self.event1

        detail_button = row0.locator("a[aria-label='Ver Detalle']")
        edit_button = row0.locator("a[aria-label='Editar']")
        delete_form = row0.locator("form")

        expect(detail_button).to_be_visible()
        expect(detail_button).to_have_attribute("href", f"/events/{event.id}/")

        if user_type == "organizador":
            expect(edit_button).to_be_visible()
            expect(edit_button).to_have_attribute("href", f"/events/{event.id}/edit/")

            expect(delete_form).to_have_attribute("action", f"/events/{event.id}/delete/")
            expect(delete_form).to_have_attribute("method", "POST")

            delete_button = delete_form.locator("button[aria-label='Eliminar']")
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

        # Esperar a que la página cargue completamente
        self.page.wait_for_load_state("networkidle")

        # Verificar el título de la página
        expect(self.page).to_have_title("Eventos")

        # Verificar que existe un encabezado con el texto "Eventos"
        header = self.page.locator("h1")
        expect(header).to_have_text("Eventos")
        expect(header).to_be_visible()

        # Verificar que existe una tabla
        table = self.page.locator("table")
        expect(table).to_be_visible()

        # Verificar que el toggle existe y está desactivado por defecto
        toggle = self.page.locator("#showPastEvents")
        expect(toggle).to_be_visible()
        expect(toggle).not_to_be_checked()

        # Verificar contenido inicial (sin eventos pasados)
        self._table_has_event_info(show_past=False)
        self._table_has_correct_actions("organizador", show_past=False)

        # Activar el toggle para mostrar eventos pasados
        toggle.click()

        # Esperar a que la página cargue completamente después del cambio
        self.page.wait_for_load_state("networkidle")

        # Verificar contenido con eventos pasados
        self._table_has_event_info(show_past=True)
        self._table_has_correct_actions("organizador", show_past=True)

        # Desactivar el toggle
        toggle.click()

        # Esperar a que la página cargue completamente después del cambio
        self.page.wait_for_load_state("networkidle")

        # Verificar que volvemos a mostrar solo eventos futuros
        self._table_has_event_info(show_past=False)
        self._table_has_correct_actions("organizador", show_past=False)

    def test_events_page_no_events(self):
        """Test que verifica el comportamiento cuando no hay eventos"""
        # Eliminar todos los eventos
        Event.objects.all().delete()

        self.login_user("organizador", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        # Esperar a que la página cargue completamente
        self.page.wait_for_load_state("networkidle")

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

        # Esperar a que la página cargue completamente
        self.page.wait_for_load_state("networkidle")

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
        self.page.get_by_label("Fecha").fill("2025-06-15")
        self.page.get_by_label("Hora").fill("16:45")
        self.page.get_by_label("Precio General").fill("100.00")
        self.page.get_by_label("Precio VIP").fill("200.00")
        self.page.get_by_label("Cantidad de entradas").fill("1000")

        # Enviar el formulario
        self.page.get_by_role("button", name="Crear Evento").click()

        # Esperar a que la página cargue completamente
        self.page.wait_for_load_state("networkidle")

        # Verificar que redirigió a la página de eventos
        expect(self.page).to_have_url(f"{self.live_server_url}/events/")

        # Verificar que el nuevo evento está en la lista
        expect(self.page.locator("text=Evento de prueba E2E")).to_be_visible()

    def test_edit_event_organizer(self):
        """Test que verifica la funcionalidad de editar un evento para organizadores"""
        # Iniciar sesión como organizador
        self.login_user("organizador", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        # Esperar a que la página cargue completamente
        self.page.wait_for_load_state("networkidle")

        # Debug: Verificar estado del toggle
        toggle = self.page.locator("#showPastEvents")
        
        # Debug: Imprimir eventos antes de editar
        rows = self.page.locator("table tbody tr")
        for i in range(rows.count()):
            row = rows.nth(i)
            title = row.locator("td").nth(0).inner_text()
            description = row.locator("td").nth(1).inner_text()
            date = row.locator("td").nth(2).inner_text()

        # Hacer clic en el botón de editar del primer evento
        edit_link = self.page.locator("table tbody tr").first.locator("a[aria-label='Editar']")
        expect(edit_link).to_be_visible()
        edit_link.click()

        # Esperar a que la página de edición cargue completamente
        self.page.wait_for_load_state("networkidle")

        # Verificar que estamos en la página de edición
        expect(self.page).to_have_url(f"{self.live_server_url}/events/{self.event1.id}/edit/")

        # Verificar que el formulario está precargado con los datos del evento
        title = self.page.get_by_label("Título del Evento")
        expect(title).to_have_value("Evento de prueba 1")
        title.fill("Titulo editado")

        description = self.page.get_by_label("Descripción")
        expect(description).to_have_value("Descripción del evento 1")
        description.fill("Descripcion Editada")

        # Verificar que la fecha tiene el formato correcto (YYYY-MM-DD)
        date = self.page.get_by_label("Fecha")
        date_value = date.input_value()
        assert re.match(r"\d{4}-\d{2}-\d{2}", date_value)
        date.fill("2025-04-20")

        # Verificar que la hora tiene el formato correcto (HH:MM)
        time = self.page.get_by_label("Hora")
        time_value = time.input_value()
        assert re.match(r"\d{2}:\d{2}", time_value)
        time.fill("03:00")

        # Enviar el formulario
        submit_button = self.page.get_by_role("button", name="Crear Evento")
        expect(submit_button).to_be_visible()
        submit_button.click()

        # Esperar a que la página cargue completamente
        self.page.wait_for_load_state("networkidle")

        # Debug: Verificar la URL después de enviar
        current_url = self.page.url

        # Verificar que redirigió a la página de eventos
        expect(self.page).to_have_url(f"{self.live_server_url}/events/")

        # Debug: Verificar estado del toggle después de editar
        toggle = self.page.locator("#showPastEvents")

        # Esperar a que la tabla esté visible
        table = self.page.locator("table")
        expect(table).to_be_visible()

        # Esperar a que los eventos estén cargados
        self.page.wait_for_selector("table tbody tr")

        # Debug: Imprimir información de los eventos en la tabla
        rows = self.page.locator("table tbody tr")
        for i in range(rows.count()):
            row = rows.nth(i)
            title = row.locator("td").nth(0).inner_text()
            description = row.locator("td").nth(1).inner_text()
            date = row.locator("td").nth(2).inner_text()

        # Verificar que el evento original ya no está
        expect(self.page.locator("text=Evento de prueba 1")).not_to_be_visible()

        # Activar el toggle para mostrar eventos pasados
        toggle.click()
        self.page.wait_for_load_state("networkidle")

        # Debug: Imprimir eventos después de activar el toggle
        rows = self.page.locator("table tbody tr")
        for i in range(rows.count()):
            row = rows.nth(i)
            title = row.locator("td").nth(0).inner_text()
            description = row.locator("td").nth(1).inner_text()
            date = row.locator("td").nth(2).inner_text()

        # Buscar el evento editado en la tabla (sin depender de su posición)
        event_row = self.page.locator("table tbody tr").filter(has_text="Titulo editado")
        expect(event_row).to_be_visible()

        # Verificar los detalles del evento editado
        expect(event_row.locator("td").nth(1)).to_have_text("Descripcion Editada")
        date_text = event_row.locator("td").nth(2).inner_text()
        assert re.match(r"20 abr 2025, 03:00", date_text)

        # Verificar que el evento editado aparece después del evento 2 (porque su fecha es anterior)
        rows = self.page.locator("table tbody tr")
        event2_row = rows.filter(has_text="Evento de prueba 2")
        edited_row = rows.filter(has_text="Titulo editado")
        
        # Obtener las posiciones de las filas
        event2_index = rows.evaluate_all("(rows) => rows.findIndex(row => row.textContent.includes('Evento de prueba 2'))")
        edited_index = rows.evaluate_all("(rows) => rows.findIndex(row => row.textContent.includes('Titulo editado'))")
        
        # Verificar que el evento editado está después del evento 2
        assert edited_index > event2_index, "El evento editado debería aparecer después del evento 2"

    def test_delete_event_organizer(self):
        """Test que verifica la funcionalidad de eliminar un evento para organizadores"""
        # Iniciar sesión como organizador
        self.login_user("organizador", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        # Esperar a que la página cargue completamente
        self.page.wait_for_load_state("networkidle")

        # Hacer clic en el botón de eliminar del primer evento
        delete_form = self.page.locator("table tbody tr").first.locator("form[action*='/delete/']")
        expect(delete_form).to_be_visible()
        delete_form.locator("button[aria-label='Eliminar']").click()

        # Esperar a que la página cargue completamente
        self.page.wait_for_load_state("networkidle")

        # Verificar que redirigió a la página de eventos
        expect(self.page).to_have_url(f"{self.live_server_url}/events/")

        # Verificar que el evento ya no está en la lista
        expect(self.page.locator("text=Evento de prueba 1")).not_to_be_visible()