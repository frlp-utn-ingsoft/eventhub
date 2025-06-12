import re
from playwright.sync_api import expect
from django.utils import timezone
from datetime import timedelta
from app.models import User, Event, Venue, Ticket, SatisfactionSurvey
from .base import BaseE2ETest


class SatisfactionSurveyE2ETest(BaseE2ETest):
    """Tests end-to-end para la funcionalidad completa de satisfaction survey usando Playwright"""
    
    def setUp(self):
        """Configuración inicial para los tests e2e"""
        super().setUp()
        
        # Usuario regular
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_organizer=False
        )
        
        # Usuario organizador
        self.organizer = User.objects.create_user(
            username='organizer',
            email='organizer@example.com',
            password='testpass123',
            is_organizer=True
        )
        
        # Venue para eventos
        self.venue = Venue.objects.create(
            name='Test Venue',
            adress='Test Address',
            city='Test City',
            capacity=100,
            contact='test@venue.com'
        )
        
        # Evento para encuestas
        self.event = Event.objects.create(
            title='Test Event',
            description='Event for survey testing',
            scheduled_at=timezone.now() + timedelta(days=30),
            organizer=self.organizer,
            venue=self.venue
        )

        # Crear todos los tickets necesarios para los tests
        self.base_ticket = Ticket.objects.create(
            quantity=1,
            type='GENERAL',
            event=self.event,
            user=self.user
        )

        self.vip_ticket = Ticket.objects.create(
            quantity=3,
            type='VIP',
            event=self.event,
            user=self.user
        )

        self.new_ticket = Ticket.objects.create(
            quantity=1,
            type='VIP',
            event=self.event,
            user=self.user
        )

        self.interactive_ticket = Ticket.objects.create(
            quantity=2,
            type='VIP',
            event=self.event,
            user=self.user
        )

    def test_complete_satisfaction_survey_user_journey(self):
        """Test del flujo completo de usuario completando encuesta usando Playwright"""
        # Login del usuario usando el método helper
        self.login_user('testuser', 'testpass123')
        
        # Navegar a la encuesta de satisfacción (URL real)
        self.page.goto(f"{self.live_server_url}/tickets/{self.base_ticket.pk}/survey/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que la página de encuesta cargó correctamente
        expect(self.page.locator("h3")).to_contain_text("Encuesta de Satisfacción")
        expect(self.page.locator("strong").filter(has_text="Test Event")).to_be_visible()
        
        # Verificar que los elementos del formulario están presentes (elementos reales)
        expect(self.page.locator("input[name='overall_satisfaction']").first).to_be_visible()
        expect(self.page.locator("select[name='purchase_experience']")).to_be_visible()
        expect(self.page.locator("input[name='would_recommend']").first).to_be_visible()
        expect(self.page.locator("textarea[name='comments']")).to_be_visible()
        
        # Llenar el formulario de encuesta (usando elementos reales)
        self.page.check("input[name='overall_satisfaction'][value='5']")
        self.page.select_option("select[name='purchase_experience']", "facil")
        self.page.check("input[name='would_recommend'][value='yes']")
        self.page.fill("textarea[name='comments']", "Excelente experiencia de compra!")
        
        # Enviar el formulario
        self.page.click("button[type='submit']:has-text('Enviar encuesta')")
        
        # Verificar redirección exitosa (puede ser a tickets o eventos)
        self.page.wait_for_url(re.compile(r".*(tickets|events).*"), timeout=10000)
        
        # Verificar que la encuesta se guardó en la base de datos
        survey = SatisfactionSurvey.objects.get(ticket=self.base_ticket)
        self.assertEqual(survey.overall_satisfaction, 5)
        self.assertEqual(survey.purchase_experience, 'facil')
        self.assertTrue(survey.would_recommend)
        self.assertIn('Excelente', survey.comments or '')

    def test_satisfaction_survey_form_validation_errors(self):
        """Test validación de errores en el formulario usando Playwright"""
        # Login del usuario
        self.login_user('testuser', 'testpass123')
        
        # Navegar a la encuesta
        self.page.goto(f"{self.live_server_url}/tickets/{self.new_ticket.pk}/survey/")
        self.page.wait_for_load_state("networkidle")
        
        # Intentar enviar formulario sin completar campos requeridos
        self.page.click("button[type='submit']:has-text('Enviar encuesta')")
        
        # Verificar que aparecen mensajes de error o validación HTML5
        # En caso de validación HTML5, la página no se enviará
        expect(self.page).to_have_url(re.compile(f".*tickets/{self.new_ticket.pk}/survey.*"))

    def test_satisfaction_survey_ticket_information_display(self):
        """Test que verifica la información del ticket en la encuesta"""
        # Login del usuario
        self.login_user('testuser', 'testpass123')
        
        # Navegar a la encuesta
        self.page.goto(f"{self.live_server_url}/tickets/{self.vip_ticket.pk}/survey/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar información del evento y ticket
        expect(self.page.locator("strong").filter(has_text="Test Event")).to_be_visible()
        expect(self.page.locator("p").filter(has_text="3 entrada")).to_be_visible()
        expect(self.page.locator("p").filter(has_text="Tipo: VIP")).to_be_visible()

    def test_satisfaction_survey_form_elements_present(self):
        """Test que verifica que todos los elementos del formulario están presentes"""
        # Login del usuario
        self.login_user('testuser', 'testpass123')
        
        # Navegar a la encuesta usando el ticket base
        self.page.goto(f"{self.live_server_url}/tickets/{self.base_ticket.pk}/survey/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar elementos de satisfacción (radio buttons)
        for value in ['1', '2', '3', '4', '5']:
            expect(self.page.locator(f"input[name='overall_satisfaction'][value='{value}']")).to_be_visible()
        
        # Verificar dropdown de experiencia de compra
        expect(self.page.locator("select[name='purchase_experience']")).to_be_visible()
        
        # Verificar radio buttons de recomendación
        expect(self.page.locator("input[name='would_recommend'][value='yes']")).to_be_visible()
        expect(self.page.locator("input[name='would_recommend'][value='no']")).to_be_visible()
        
        # Verificar textarea de comentarios
        expect(self.page.locator("textarea[name='comments']")).to_be_visible()
        
        # Verificar botones
        expect(self.page.locator("button[type='submit']:has-text('Enviar encuesta')")).to_be_visible()
        expect(self.page.locator("a.btn:has-text('Omitir encuesta')")).to_be_visible()  # Botón "Omitir encuesta"

    def test_satisfaction_survey_responsive_design(self):
        """Test diseño responsive de la encuesta"""
        # Login del usuario
        self.login_user('testuser', 'testpass123')
        
        # Navegar a la encuesta usando el ticket base
        self.page.goto(f"{self.live_server_url}/tickets/{self.base_ticket.pk}/survey/")
        self.page.wait_for_load_state("networkidle")
        
        # Probar en viewport móvil
        self.page.set_viewport_size({"width": 375, "height": 667})
        
        # Verificar que los elementos se adaptan al móvil
        expect(self.page.locator(".container")).to_be_visible()
        expect(self.page.locator("input[name='overall_satisfaction']").first).to_be_visible()
        expect(self.page.locator("button[type='submit']:has-text('Enviar encuesta')")).to_be_visible()

    def test_satisfaction_survey_complete_form_interaction(self):
        """Test interacción completa con todos los elementos del formulario"""
        # Login del usuario
        self.login_user('testuser', 'testpass123')
        
        # Navegar a la encuesta
        self.page.goto(f"{self.live_server_url}/tickets/{self.interactive_ticket.pk}/survey/")
        self.page.wait_for_load_state("networkidle")
        
        # Probar cada nivel de satisfacción
        for satisfaction_level in ['1', '2', '3', '4', '5']:
            self.page.check(f"input[name='overall_satisfaction'][value='{satisfaction_level}']")
            expect(self.page.locator(f"input[name='overall_satisfaction'][value='{satisfaction_level}']")).to_be_checked()
        
        # Probar opciones de experiencia de compra
        experience_options = ["muy_dificil", "dificil", "normal", "facil", "muy_facil"]
        for option in experience_options:
            self.page.select_option("select[name='purchase_experience']", option)
            expect(self.page.locator("select[name='purchase_experience']")).to_have_value(option)
        
        # Probar radio buttons de recomendación
        self.page.check("input[name='would_recommend'][value='yes']")
        expect(self.page.locator("input[name='would_recommend'][value='yes']")).to_be_checked()
        
        self.page.check("input[name='would_recommend'][value='no']")
        expect(self.page.locator("input[name='would_recommend'][value='no']")).to_be_checked()
        
        # Probar textarea de comentarios
        test_comment = "Este es un comentario de prueba para verificar la funcionalidad."
        self.page.fill("textarea[name='comments']", test_comment)
        expect(self.page.locator("textarea[name='comments']")).to_have_value(test_comment)

    def test_satisfaction_survey_navigation_elements(self):
        """Test elementos de navegación en la página de encuesta"""
        # Login del usuario
        self.login_user('testuser', 'testpass123')
        
        # Navegar a la encuesta usando el ticket base
        self.page.goto(f"{self.live_server_url}/tickets/{self.base_ticket.pk}/survey/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar navbar
        expect(self.page.locator(".navbar")).to_be_visible()
        
        # Verificar breadcrumb o enlaces de navegación si existen
        breadcrumb = self.page.locator(".breadcrumb")
        if breadcrumb.count() > 0:
            expect(breadcrumb).to_be_visible()
        
        # Verificar botón de "Omitir encuesta" funciona
        omit_button = self.page.locator("a.btn:has-text('Omitir')")
        if omit_button.count() > 0:
            expect(omit_button).to_be_visible()
            expect(omit_button).to_have_attribute("href", re.compile(r".*"))

    def test_satisfaction_survey_ticket_details_section(self):
        """Test sección de detalles del ticket en la encuesta"""
        # Login del usuario
        self.login_user('testuser', 'testpass123')
        
        # Navegar a la encuesta usando el ticket base
        self.page.goto(f"{self.live_server_url}/tickets/{self.base_ticket.pk}/survey/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar información del evento
        expect(self.page.locator("strong").filter(has_text="Test Event")).to_be_visible()
        
        # Verificar información del ticket
        expect(self.page.locator("p").filter(has_text="1 entrada")).to_be_visible()
        expect(self.page.locator("p").filter(has_text="Tipo: GENERAL")).to_be_visible()
        
        # Verificar información del venue si se muestra
        venue_info = self.page.locator("p").filter(has_text="Test Venue")
        if venue_info.count() > 0:
            expect(venue_info).to_be_visible()

    def test_satisfaction_survey_success_purchase_message(self):
        """Test mensaje de éxito después de completar encuesta"""
        # Login del usuario
        self.login_user('testuser', 'testpass123')
        
        # Navegar a la encuesta usando el ticket base
        self.page.goto(f"{self.live_server_url}/tickets/{self.base_ticket.pk}/survey/")
        self.page.wait_for_load_state("networkidle")
        
        # Completar y enviar formulario
        self.page.check("input[name='overall_satisfaction'][value='4']")
        self.page.select_option("select[name='purchase_experience']", "facil")
        self.page.check("input[name='would_recommend'][value='yes']")
        self.page.fill("textarea[name='comments']", "Buen servicio en general")
        
        # Enviar formulario
        self.page.click("button[type='submit']:has-text('Enviar encuesta')")
        
        # Esperar redirección
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que estamos en una página de éxito (puede variar según implementación)
        # Verificar elementos comunes de éxito como mensajes flash o confirmación
        success_indicators = [
            "Gracias por tu opinión",
            "Encuesta enviada",
            "Agradecemos tu feedback",
            "Tu opinión es importante"
        ]
        
        page_content = self.page.content()
        success_found = any(indicator in page_content for indicator in success_indicators)
        
        # Si no hay mensaje de éxito específico, al menos verificar que no estamos en la misma página de encuesta
        if not success_found:
            current_url = self.page.url
            self.assertNotIn(f"/tickets/{self.base_ticket.pk}/survey/", current_url) 