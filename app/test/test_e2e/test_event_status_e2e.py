import datetime
import re

from playwright.sync_api import expect
from django.urls import reverse
from django.utils import timezone

from app.models import Event, User
from category.models import Category
from app.test.test_e2e.base import BaseE2ETest


class EventStatusE2ETest(BaseE2ETest):
    """
    Tests E2E específicos para verificar la funcionalidad de status de eventos
    a través de la interfaz de usuario
    """

    def setUp(self):
        super().setUp()

        # Crear usuario y categoría para cada test.
        self.organizer = User.objects.create_user(username='e2e_org_status', password='password123', is_organizer=True)
        self.organizer.email = 'e2e_org_status@example.com'
        self.organizer.save()
        self.category = Category.objects.create(name='E2E Status Category', is_active=True)

    def tearDown(self):
        Event.objects.filter(title__startswith="E2E Test Event with Status Creation").delete()
        Event.objects.filter(title__startswith="E2E Event for Status Edit").delete()

        super().tearDown()

    def login_user(self, username, password):
        """
        Método auxiliar para iniciar sesión un usuario
        """
        self.page.goto(self.live_server_url + reverse('login'))
        self.page.fill("input[name='username']", username)
        self.page.fill("input[name='password']", password)
        self.page.click("button[type='submit']")

        expect(self.page).to_have_url(re.compile(self.live_server_url + reverse('events') + r"$"), timeout=10000)


    def test_organizer_can_create_and_view_event_with_status(self):
        """
        Verifica que un organizador puede crear un evento con un status específico
        y que este se muestra correctamente en la lista y detalle
        """
        self.login_user(self.organizer.username, "password123")

        # Navegar a la página de creación de evento
        self.page.goto(self.live_server_url + reverse('event_form'))
        self.page.wait_for_load_state('domcontentloaded')

        expect(self.page).to_have_url(re.compile(self.live_server_url + reverse('event_form') + r"$"))

        # Llenar el formulario
        event_title = "E2E Test Event with Status Creation"
        self.page.fill("input[name='title']", event_title)
        self.page.fill("textarea[name='description']", "Description for E2E Test Event creation.")

        future_date = (timezone.now() + datetime.timedelta(days=10)).strftime('%Y-%m-%d')
        future_time = "10:00"
        self.page.fill("input[name='date']", future_date)
        self.page.fill("input[name='time']", future_time)

        # Seleccionar categoría (checkbox)
        category_checkbox_selector = f"input[name='categories'][value='{self.category.id}']"
        self.page.locator(category_checkbox_selector).wait_for(state='visible')
        self.page.locator(category_checkbox_selector).check()

        # Seleccionar el status 'reprogramado'
        self.page.locator("select[name='status']").select_option(value='reprogramado')

        # Enviar el formulario
        self.page.click("button[type='submit'][name='Guardar']")

        self.page.wait_for_url(re.compile(self.live_server_url + reverse('events') + r"$"), timeout=10000)

        expect(self.page).to_have_url(re.compile(self.live_server_url + reverse('events') + r"$"))
        expect(self.page.locator(f"text={event_title}")).to_be_visible()

        # Verificar que el status se muestra correctamente en la tabla (5ta columna, indice 4)
        row_locator = self.page.locator(f"//tr[contains(td[1], '{event_title}')]")
        expect(row_locator.locator("td:nth-child(5)")).to_have_text("Reprogramado")

        # Ir a la página de detalle del evento
        # hace clic en el boton "Ver detalle" dentro de la fila específica
        row_locator.locator("a[aria-label='Ver detalle']").click()

        self.page.wait_for_load_state('domcontentloaded')
        # Verificar la navegación a la página de detalle del evento
        expect(self.page).to_have_url(re.compile(r'/events/\d+/$'))

        # Verificar que el status se muestra correctamente en la pagina de detalle
        expect(self.page.locator("p:has-text('Estado: Reprogramado')")).to_be_visible()


    def test_organizer_can_edit_event_status(self):
        """
        Verifica que un organizador puede editar el status de un evento existente
        y que el cambio se refleja en la interfaz
        """
        event_title_to_edit = "E2E Event for Status Edit"
        event_to_edit = Event.objects.create(
            title=event_title_to_edit,
            description="Original description for edit test.",
            scheduled_at=timezone.now() + datetime.timedelta(days=15),
            organizer=self.organizer,
            status='activo'
        )
        event_to_edit.categories.add(self.category)

        self.login_user(self.organizer.username, "password123")

        self.page.goto(self.live_server_url + reverse('events'))
        self.page.wait_for_load_state('domcontentloaded')

        # Localizar la fila del evento a editar
        row_locator_edit = self.page.locator(f"//tr[contains(td[1], '{event_title_to_edit}')]")
        expect(row_locator_edit).to_be_visible()

        # Hacer clic en el botón "Editar" para el evento especifico
        edit_button_selector = "a[aria-label='Editar']"
        edit_link_locator = row_locator_edit.locator(edit_button_selector)

        expected_edit_url_path = edit_link_locator.get_attribute('href')
        self.assertIsNotNone(expected_edit_url_path, "No se encontró el atributo href para el enlace de edición.")

        edit_link_locator.click()

        self.page.wait_for_load_state('domcontentloaded')
        expect(self.page).to_have_url(re.compile(self.live_server_url + expected_edit_url_path + r"$"))

        # Seleccionar el nuevo status 'cancelado'
        self.page.locator("select[name='status']").wait_for(state='visible')
        self.page.locator("select[name='status']").select_option(value='cancelado')

        # Enviar el formulario
        self.page.click("button[type='submit'][name='Guardar']")

        self.page.wait_for_url(re.compile(self.live_server_url + reverse('events') + r"$"), timeout=10000)

        expect(self.page).to_have_url(re.compile(self.live_server_url + reverse('events') + r"$"))

        # Activar el switch para mostrar eventos pasados/cancelados
        self.page.locator("#showPastSwitch").check()
        self.page.wait_for_url(re.compile(self.live_server_url + reverse('events_all') + r"$"), timeout=10000)

        expect(self.page.locator(f"text={event_title_to_edit}")).to_be_visible()

        # Verificar que el nuevo status se muestra en la tabla
        row_locator_after_edit = self.page.locator(f"//tr[contains(td[1], '{event_title_to_edit}')]")
        expect(row_locator_after_edit.locator("td:nth-child(5)")).to_have_text("Cancelado")

        # Ir a la pagina de detalle del evento
        row_locator_after_edit.locator("a[aria-label='Ver detalle']").click()

        self.page.wait_for_load_state('domcontentloaded')
        expect(self.page).to_have_url(re.compile(r'/events/\d+/$'))

        # Verificar que el status actualizado se muestra en la pagina de detalle
        expect(self.page.locator("p:has-text('Estado: Cancelado')")).to_be_visible()