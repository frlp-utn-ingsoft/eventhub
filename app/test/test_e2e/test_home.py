import re
import time

from playwright.sync_api import expect

from app.test.test_e2e.base import BaseE2ETest


# Tests para la página de inicio
class HomePageDisplayTest(BaseE2ETest):
    """Tests relacionados con la visualización de la página de inicio"""

    def test_home_page_loads(self):
        """Test que verifica que la home carga correctamente"""
        self.page.goto(f"{self.live_server_url}/")

        # Verificar que el logo este presente
        logo = self.page.get_by_text("EventHub", exact=True)
        expect(logo).to_be_visible()
        expect(logo).to_have_attribute("href", "/")

        # Verificar textos principales de la página
        expect(self.page.get_by_text("Eventos y Entradas")).to_be_visible()
        expect(
            self.page.get_by_text(
                "Descubre, organiza y participa en los mejores eventos. Compra entradas, deja comentarios y califica tus experiencias."
            )
        ).to_be_visible()


class HomeNavigationTest(BaseE2ETest):
    """Tests relacionados con la navegación desde la página de inicio"""

    def test_login_button_navigates_to_login_page(self):
        """Test que verifica que el botón de login navega a la página de login"""
        self.page.goto(f"{self.live_server_url}/")
        self.page.get_by_role("link", name="Ingresá").click()
        expect(self.page).to_have_url(re.compile(".*/login"))


class HomeAuthenticationTest(BaseE2ETest):
    """Tests relacionados con el comportamiento de autenticación en la página de inicio"""

    def test_auth_buttons_visibility_for_anonymous_user(self):
        """Test que verifica la visibilidad de los botones para usuarios anónimos"""
        self.page.goto(f"{self.live_server_url}/")

        # Verificar que el botón de iniciar sesión esté presente
        login_btn = self.page.get_by_role("link", name="Ingresá")
        expect(login_btn).to_be_visible()

        # Verificar que el botón de crear cuenta esté presente
        signup_btn = self.page.get_by_role("link", name="Creá tu cuenta")
        expect(signup_btn).to_be_visible()

        # Verificar que el botón de cerrar sesión no esté presente
        logout_btn = self.page.get_by_role("button", name="Salir")
        expect(logout_btn).to_have_count(0)

    def test_auth_buttons_visibility_for_authenticated_user(self):
        """Test que verifica la visibilidad de los botones para usuarios autenticados"""
        # Crear usuario y autenticarlo
        user = self.create_test_user()

        # Ir a la página de inicio y luego iniciar sesión
        self.page.goto(f"{self.live_server_url}/")
        self.page.get_by_role("link", name="Ingresá").click()

        # Llenar el formulario con credenciales válidas
        self.page.get_by_label("Usuario").fill(user.username)
        self.page.get_by_label("Contraseña").fill("password123")

        # Enviar el formulario
        self.page.get_by_role("button", name="Iniciar sesión").click()

        # Verificar que el botón de iniciar sesión no esté presente
        login_btn = self.page.get_by_role("link", name="Ingresá")
        expect(login_btn).to_have_count(0)

        # Verificar que el botón de crear cuenta no esté presente
        signup_btn = self.page.get_by_role("link", name="Creá tu cuenta")
        expect(signup_btn).to_have_count(0)

        # Verificar que el botón de cerrar sesión esté presente
        logout_btn = self.page.get_by_role("button", name="Salir")
        expect(logout_btn).to_be_visible()


class HomeThemeTest(BaseE2ETest):
    """Tests sobre el tema de la página de inicio"""

    def test_prefer_color_scheme(self):
        """Test que verifica que el tema inicial es el esperado y se setea correctamente"""

        # Inicial en dark
        context = self.browser.new_context(color_scheme="dark")
        page = context.new_page()
        page.goto(f"{self.live_server_url}/")

        # Recupera el atributo data-bs-theme del html
        theme_attr = page.evaluate("document.documentElement.getAttribute('data-bs-theme')")
        assert theme_attr == "dark", (
            f"El valor seteado en el html: '{theme_attr}' es distinto a la preferencia del usuario: 'dark'"
        )

        # Inicial en light
        context = self.browser.new_context(color_scheme="light")
        page = context.new_page()
        page.goto(f"{self.live_server_url}/")

        theme_attr = page.evaluate("document.documentElement.getAttribute('data-bs-theme')")
        assert theme_attr == "light", (
            f"El valor seteado en el html: '{theme_attr}' es distinto a la preferencia del usuario: 'light'"
        )

        # Inicial en None
        context = self.browser.new_context(color_scheme=None)
        page = context.new_page()
        page.goto(f"{self.live_server_url}/")

        theme_attr = page.evaluate("document.documentElement.getAttribute('data-bs-theme')")
        assert theme_attr == "light", (
            f"El valor seteado en el html: '{theme_attr}' por defecto debe ser 'light'"
        )

    def test_toggle_theme(self):
        """Test que verifica que el botón alterna tema claro a oscuro correctamente"""

        self.page.goto(f"{self.live_server_url}/")

        button_theme_toggle = self.page.locator("#themeToggle")
        initial_theme_attr = self.page.evaluate(
            "document.documentElement.getAttribute('data-bs-theme')"
        )
        button_theme_toggle.click()
        final_theme_attr = self.page.evaluate(
            "document.documentElement.getAttribute('data-bs-theme')"
        )
        assert initial_theme_attr != final_theme_attr, (
            "El tema no cambió al hacer clic en el botón de alternar tema"
        )
