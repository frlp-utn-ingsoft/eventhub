import datetime
import re

from django.test import TestCase
from django.utils import timezone
from playwright.sync_api import expect

from app.models import Event, User, Venue
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

        # Crear eventos de prueba
        # Evento 1
        event_date1 = timezone.make_aware(datetime.datetime(2025, 2, 10, 10, 10))
        self.event1 = Event.objects.create(
            title="Evento de prueba 1",
            description="Descripción del evento 1",
            scheduled_at=event_date1,
            organizer=self.organizer,
        )

        # Evento 2
        event_date2 = timezone.make_aware(datetime.datetime(2025, 3, 15, 14, 30))
        self.event2 = Event.objects.create(
            title="Evento de prueba 2",
            description="Descripción del evento 2",
            scheduled_at=event_date2,
            organizer=self.organizer,
        )
        
        self.venue = Venue.objects.create(
            user=self.organizer,
            name="Sala de Eventos",
            address="Calle Falsa 123",
            city="Ciudad",
            capacity=100,
            contact="Contacto de prueba",
        )

    def _table_has_event_info(self):
        """Método auxiliar para verificar que la tabla tiene la información correcta de eventos"""
        # Verificar encabezados de la tabla
        headers = self.page.locator("table thead th")
        expect(headers.nth(0)).to_have_text("Título")
        expect(headers.nth(1)).to_have_text("Descripción")
        expect(headers.nth(2)).to_have_text("Fecha")
        expect(headers.nth(3)).to_have_text("Categorias")
        expect(headers.nth(4)).to_have_text("Lugar")
        expect(headers.nth(5)).to_have_text("Acciones")

        # Click en el dropdown "Filtros"
        self.page.get_by_role("button", name="Filtros").click()

        checkbox = self.page.locator("#past_events")
        if not checkbox.is_checked():
            checkbox.click()

        # Click en el botón "Aplicar filtros" dentro del dropdown
        self.page.locator("#apply_filters").click()

        # Verificar que los eventos aparecen en la tabla
        rows = self.page.locator("table tbody tr")
        expect(rows).to_have_count(2)

        # Verificar datos del primer evento
        row0 = rows.nth(0)
        expect(row0.locator("td").nth(0)).to_have_text("Evento de prueba 1")
        expect(row0.locator("td").nth(1)).to_have_text("Descripción del evento 1")
        expect(row0.locator("td").nth(2)).to_have_text("10 feb 2025, 10:10")

        # Verificar datos del segundo evento
        expect(rows.nth(1).locator("td").nth(0)).to_have_text("Evento de prueba 2")
        expect(rows.nth(1).locator("td").nth(1)).to_have_text("Descripción del evento 2")
        expect(rows.nth(1).locator("td").nth(2)).to_have_text("15 mar 2025, 14:30")

    def _table_has_correct_actions(self, user_type):
        """Método auxiliar para verificar que las acciones son correctas según el tipo de usuario"""
        row0 = self.page.locator("table tbody tr").nth(0)

        detail_button = row0.get_by_role("link", name="Ver Detalle")
        edit_button = row0.get_by_role("link", name="Editar")
        # Seleccionar el formulario de eliminación del primer evento
        delete_form = self.page.locator(f"#deleteModal{self.event1.id} form")

        expect(detail_button).to_be_visible()
        expect(detail_button).to_have_attribute("href", f"/events/{self.event1.id}/")

        if user_type == "organizador":
            expect(edit_button).to_be_visible()
            expect(edit_button).to_have_attribute("href", f"/events/{self.event1.id}/edit/")

            expect(delete_form).to_have_attribute("action", f"/events/{self.event1.id}/delete/")
            expect(delete_form).to_have_attribute("method", "POST")

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

    def test_button_filter_my_events(self):
        """Test que verifica que el boton de filtro Mis eventos no es visible para el usuario regular y es visible para el usuario administrador"""
        # Primero verificar como usuario normal
        self.login_user("usuario", "password123")
        self.page.goto(f"{self.live_server_url}/events/")

        # Click en el dropdown "Filtros"
        self.page.get_by_role("button", name="Filtros").click()
        checkbox = self.page.locator("#my_events")

        # Verificar que NO existe la checkbox de "Mis Eventos"
        expect(checkbox).to_have_count(0)

        # Cerrar sesión
        self.page.get_by_role("button", name="Salir").click()

        # Iniciar sesión como usuario organizador
        self.login_user("organizador", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        # Click en el dropdown "Filtros"
        self.page.get_by_role("button", name="Filtros").click()

        checkbox = self.page.locator("#my_events")
        # Verificar que existe la checkbox de "Mis Eventos"
        expect(checkbox).to_have_count(1)


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

        expect(self.page.get_by_role("heading", name="Crear evento")).to_be_visible()

        # Completar el formulario
        
        # Elegimos una nueva fecha/hora basada en timezone.now()
        future_dt = timezone.now() + datetime.timedelta(days=5, hours=4, minutes=15)
        date_str = future_dt.date().isoformat()          # 'YYYY-MM-DD'
        time_str = future_dt.time().strftime("%H:%M")    # 'HH:MM'
        
        self.page.get_by_label("Título del Evento").fill("Evento de prueba E2E")
        # Esperar a que el campo descripción esté visible (único dentro del div)
        self.page.locator("#description_event >> textarea#description").wait_for(state="visible")

        # Llenar el campo
        self.page.locator("#description_event >> textarea#description").fill(
            "Descripción creada desde prueba E2E"
        )
        self.page.get_by_label("Fecha").fill(date_str)

        self.page.get_by_label("Hora").fill(time_str)
        
        self.page.select_option("#venue_id", str(self.venue.id))

        # Enviar el formulario
        self.page.get_by_role("button", name="Crear Evento").click()

        # Verificar que redirigió a la página de eventos
        expect(self.page).to_have_url(f"{self.live_server_url}/events/")

        # Click en el dropdown "Filtros"
        self.page.get_by_role("button", name="Filtros").click()

        checkbox = self.page.locator("#past_events")
        if not checkbox.is_checked():
            checkbox.click()

        # Click en el botón "Aplicar filtros" dentro del dropdown
        self.page.locator("#apply_filters").click()

        # Verificar que ahora hay 3 eventos
        rows = self.page.locator("table tbody tr")
        expect(rows).to_have_count(3)

        row = self.page.locator("table tbody tr").last
        expect(row.locator("td").nth(0)).to_have_text("Evento de prueba E2E")
        expect(row.locator("td").nth(1)).to_have_text("Descripción creada desde prueba E2E")
        # Verificar que la celda muestra la hora correcta
        expect(row.locator("td").nth(2)).to_contain_text(time_str)

        # Verificar que incluye día y año 
        cell_text = row.locator("td").nth(2).text_content()
        assert str(future_dt.day) in cell_text
        assert str(future_dt.year) in cell_text

    def test_visibility_countdown_event(self):
        """Test que verifica que el countdown del detalle de evento es visible para el usuario regular y no para el usuario organizador"""

        event3 = Event.objects.create(
            title="Evento de prueba 3",
            description="Descripción del evento 3 con fecha futura",
            scheduled_at=timezone.now() + datetime.timedelta(days=3, hours=3, minutes=30),
            organizer=self.organizer,
        )

        # Iniciar sesión como usuario organizador
        self.login_user("organizador", "password123")

        # Ir a la página de detalle del evento 3
        self.page.goto(f"{self.live_server_url}/events/{event3.id}")

        # Seleccionar el div del countdown
        countdown = self.page.locator("#div-countdown")

        # Verificar que countdown no es visible para el organizador
        expect(countdown, "El Contdown no debe ser visible para el organizador").to_have_count(0)

        # Cerrar sesión
        self.logout_user()

        # Iniciar sesión como usuario normal
        self.login_user("usuario", "password123")
        self.page.goto(f"{self.live_server_url}/events/{event3.id}")
        countdown = self.page.locator("#div-countdown")
        # Verificar que countdown es visible para el usuario normal
        expect(countdown, "El Contdown debe ser visible para el usuario normal").to_have_count(1)

    def test_countdown_event(self):
        """Test que verifica que el countdown del detalle de evento calcula bien el tiempo restante"""

        scheduled_at= timezone.now() + datetime.timedelta(days=1)

        event3 = Event.objects.create(
            title="Evento de prueba 3",
            description="Descripción del evento 3, comienza en 1 dia",
            scheduled_at=scheduled_at,
            organizer=self.organizer,
        )

        # Iniciar sesión como usuario normal
        self.login_user("usuario", "password123")
        self.page.goto(f"{self.live_server_url}/events/{event3.id}")

        h4_countdown = self.page.locator("h4#countdown")
        # formato `${days}d ${hours}h ${minutes}m ${seconds}s`
        expect(h4_countdown).to_have_text(re.compile(r"^0d 23h 59m"))

    def test_edit_event_organizer(self):
        """Test que verifica la funcionalidad de editar un evento para organizadores"""
        # Iniciar sesión como organizador
        self.login_user("organizador", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")
        # Click en el dropdown "Filtros"
        self.page.get_by_role("button", name="Filtros").click()

        checkbox = self.page.locator("#past_events")
        if not checkbox.is_checked():
            checkbox.click()

        # Click en el botón "Aplicar filtros" dentro del dropdown
        self.page.locator("#apply_filters").click()

        # Hacer clic en el botón editar del primer evento
        self.page.get_by_role("link", name="Editar").first.click()

        # Verificar que estamos en la página de edición
        expect(self.page).to_have_url(f"{self.live_server_url}/events/{self.event1.id}/edit/")

        expect(self.page.get_by_text("Editar evento")).to_be_visible()

        # Verificar que el formulario está precargado con los datos del evento y luego los editamos
        title = self.page.get_by_label("Título del Evento")
        expect(title).to_have_value("Evento de prueba 1")
        title.fill("Titulo editado")

        # Esperar a que el campo descripción esté visible (único dentro del div)
        self.page.locator("#description_event >> textarea#description").wait_for(state="visible")

        # Llenar el campo
        # Elegimos una nueva fecha/hora basada en timezone.now()
        future_dt = timezone.now() + datetime.timedelta(days=5, hours=4, minutes=15)
        date_str = future_dt.date().isoformat()          # 'YYYY-MM-DD'
        time_str = future_dt.time().strftime("%H:%M")    # 'HH:MM'
        
        description = self.page.locator("#description_event >> textarea#description")
        expect(description).to_have_value("Descripción del evento 1")
        description.fill("Descripción Editada")

        date = self.page.get_by_label("Fecha")
        expect(date).to_have_value("2025-02-10")
        date.fill(date_str)

        time = self.page.get_by_label("Hora")
        expect(time).to_have_value("10:10")
        time.fill(time_str)
        
        self.page.select_option("#venue_id", str(self.venue.id))

        # Enviar el formulario
        self.page.get_by_role("button", name="Guardar").click()

        # Verificar que redirigió a la página de eventos
        expect(self.page).to_have_url(f"{self.live_server_url}/events/")
        # Click en el dropdown "Filtros"
        self.page.get_by_role("button", name="Filtros").click()

        checkbox = self.page.locator("#past_events")
        if not checkbox.is_checked():
            checkbox.click()

        # Click en el botón "Aplicar filtros" dentro del dropdown
        self.page.locator("#apply_filters").click()

        # Verificar que el título del evento ha sido actualizado
        row = self.page.locator("table tbody tr").last
        expect(row.locator("td").nth(0)).to_have_text("Titulo editado")
        expect(row.locator("td").nth(1)).to_have_text("Descripción Editada")
        
        # Verificar que la celda muestra la hora correcta
        expect(row.locator("td").nth(2)).to_contain_text(time_str)

        # Verificar que incluye día y año (por ej. "15" y "2025")
        cell_text = row.locator("td").nth(2).text_content()
        assert str(future_dt.day) in cell_text
        assert str(future_dt.year) in cell_text

    def test_delete_event_organizer(self):
        """Test que verifica la funcionalidad de eliminar un evento para organizadores"""
        # Iniciar sesión como organizador
        self.login_user("organizador", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        # Click en el dropdown "Filtros"
        self.page.get_by_role("button", name="Filtros").click()

        checkbox = self.page.locator("#past_events")
        if not checkbox.is_checked():
            checkbox.click()

        # Click en el botón "Aplicar filtros" dentro del dropdown
        self.page.locator("#apply_filters").click()

        # Contar eventos antes de eliminar
        initial_count = len(self.page.locator("table tbody tr").all())

        row = self.page.get_by_role("row", name="Evento de prueba 1").nth(0)

        # Abrir el modal
        row.get_by_role("button", name="Eliminar").click()

        # Esperar a que el modal esté completamente visible
        self.page.locator("div[role='dialog']").wait_for(state="visible")

        # Confirmar la eliminación desde el modal
        self.page.locator("div[role='dialog']").get_by_role(
            "button", name="Eliminar", exact=True
        ).click()

        # Esperar que el evento específico ya no esté en la tabla
        expect(self.page.get_by_text("Evento de prueba 1")).to_have_count(0)

        # Esperar que el modal se cierre
        rows = self.page.locator("table tbody tr")

        # Luego esperar que la tabla tenga una fila menos
        expect(rows).to_have_count(initial_count - 1)

        # Verificar que redirigió a la página de eventos
        expect(self.page).to_have_url(f"{self.live_server_url}/events/")

        # Verificar que ahora hay un evento menos
        rows = self.page.locator("table tbody tr")
        expect(rows).to_have_count(initial_count - 1)

        # Verificar que el evento eliminado ya no aparece en la tabla
        expect(self.page.get_by_text("Evento de prueba 1")).to_have_count(0)


class EventStatusTest(EventBaseTest):
    """Estos tests se encargan especificamente de probar los estados de los eventos
    y que se muestren correctamente en la vista de detalle del evento."""

    def test_event_default_status_display(self):
        """Verificando que el estado default del evento es correcto"""
        # Iniciar sesión como organizador
        self.login_user("organizador", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        # Click en el dropdown "Filtros"
        self.page.get_by_role("button", name="Filtros").click()

        checkbox = self.page.locator("#past_events")
        if not checkbox.is_checked():
            checkbox.click()

        # Click en el botón "Aplicar filtros" dentro del dropdown
        self.page.locator("#apply_filters").click()

        # Hacer clic en el botón de detalle del evento
        self.page.get_by_role("link", name="Ver Detalle").first.click()

        # Verificar que estamos en la página de detalle del evento
        expect(self.page).to_have_url(f"{self.live_server_url}/events/{self.event1.id}/")

        # Verificar que el estado del evento es "Pendiente" inicialmente
        event_state = self.page.locator("#event-status-display")
        expect(event_state).to_have_text("Activo")

    def test_event_cancelled_status_display(self):
        """Cancelando evento y verificando que el estado se muestra correctamente"""
        # Iniciar sesión como organizador
        self.login_user("organizador", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        # Click en el dropdown "Filtros"
        self.page.get_by_role("button", name="Filtros").click()

        checkbox = self.page.locator("#past_events")
        if not checkbox.is_checked():
            checkbox.click()

        # Click en el botón "Aplicar filtros" dentro del dropdown
        self.page.locator("#apply_filters").click()

        # Hacer clic en el botón de detalle del evento
        self.page.get_by_role("link", name="Ver Detalle").first.click()

        # Verificar que estamos en la página de detalle del evento
        expect(self.page).to_have_url(f"{self.live_server_url}/events/{self.event1.id}/")

        # Cambiar el estado del evento a "Cancelado"
        cancel_button = self.page.locator("#cancel-event-button")
        cancel_button.wait_for(state="visible")

        # Primero configura el manejador para aceptar el diálogo
        self.page.once("dialog", lambda dialog: dialog.accept())
        # Luego haz clic en el botón
        cancel_button.click()

        self.page.wait_for_url(f"{self.live_server_url}/events/{self.event1.id}/")

        # Verificar que el estado del evento ahora es "Cancelado"
        event_state = self.page.locator("#event-status-display")
        event_state.wait_for(state="visible")
        expect(event_state).to_have_text("Cancelado")

    def test_event_finished_status_display(self):
        """Finalizando evento y verificando que el estado se muestra correctamente"""
        # Iniciar sesión como organizador
        self.login_user("organizador", "password123")

        # Ir a la página de eventos
        self.page.goto(f"{self.live_server_url}/events/")

        # Click en el dropdown "Filtros"
        self.page.get_by_role("button", name="Filtros").click()

        checkbox = self.page.locator("#past_events")
        if not checkbox.is_checked():
            checkbox.click()

        # Click en el botón "Aplicar filtros" dentro del dropdown
        self.page.locator("#apply_filters").click()

        # Hacer clic en el botón de detalle del evento
        self.page.get_by_role("link", name="Ver Detalle").first.click()

        # Verificar que estamos en la página de detalle del evento
        expect(self.page).to_have_url(f"{self.live_server_url}/events/{self.event1.id}/")

        # Cambiar el estado del evento a "Cancelado"
        finish_button = self.page.locator("#finish-event-button")
        finish_button.wait_for(state="visible")

        # Primero configura el manejador para aceptar el diálogo
        self.page.once("dialog", lambda dialog: dialog.accept())
        # Luego haz clic en el botón
        finish_button.click()

        self.page.wait_for_url(f"{self.live_server_url}/events/{self.event1.id}/")

        # Verificar que el estado del evento ahora es "Cancelado"
        event_state = self.page.locator("#event-status-display")
        event_state.wait_for(state="visible")
        expect(event_state).to_have_text("Finalizado")
