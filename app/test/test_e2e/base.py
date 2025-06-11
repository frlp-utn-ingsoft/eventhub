import os
import re
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from playwright.sync_api import sync_playwright

from app.models import User, Venue, Category

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
headless = os.environ.get("HEADLESS", 1) == 1
slow_mo = os.environ.get("SLOW_MO", 0)


class BaseE2ETest(StaticLiveServerTestCase):
    """Clase base con la configuración común para todos los tests E2E"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True) # 

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def setUp(self):
        # Crear un contexto y página de Playwright
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )

        # Crear venue
        self.venue = Venue.objects.create(
            name="Venue de prueba",
            adress="Dirección de prueba",
            city="Ciudad de prueba",
            capacity=100,
            contact="contacto@prueba.com"
        )

        self.regular_user = User.objects.create_user(
            username="usuario", # ¡Este es el usuario que necesitas para el login!
            email="usuario_regular@example.com",
            password="password123",
            is_organizer=False,
        )

        # Crear categoría
        self.category = Category.objects.create(
            name="Categoría de prueba",
            description="Descripción de la categoría de prueba",
            is_active=True
        )

    def tearDown(self):
        # Cerrar la página después de cada test
        self.page.close()

    def create_test_user(self, is_organizer=False):
        """Crea un usuario de prueba en la base de datos"""
        return User.objects.create_user(
            username="usuario_test",
            email="test@example.com",
            password="password123",
            is_organizer=is_organizer,
        )

    def login_user(self, username, password):
        """Método auxiliar para iniciar sesión"""
        # Ir a la página de login
        self.page.goto(f"{self.live_server_url}/accounts/login/")
        self.page.wait_for_load_state("networkidle")
        
        # Llenar el formulario
        self.page.get_by_label("Usuario").fill(username)
        self.page.get_by_label("Contraseña").fill(password)
        
        # Hacer click en el botón de login y esperar la redirección
        with self.page.expect_navigation(wait_until="networkidle") as navigation_info:
            self.page.click("button[type='submit']")
        
        # Verificar que estamos en la página de eventos
        self.page.wait_for_url(re.compile(r".*/events/?.*"), timeout=20000)
    
    def complete_card_data_in_buy_ticket_form(self):
        """
        Método auxiliar para completar el campo de las tarjetas de crédito dentro de la compra de un ticket.
        
        - Se deberá acceder a la página de compra del ticket antes de utilizar este método.
        """
        self.page.fill("#card_number", "1234567890123456")
        self.page.fill("#expiry", "12/30")
        self.page.fill("#cvv", "123")
        self.page.fill("#card_name", "Usuario Test")
        self.page.check("#terms")

