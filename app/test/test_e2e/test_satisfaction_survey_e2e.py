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

    def test_complete_satisfaction_survey_user_journey(self):
        """Test del flujo completo de usuario completando encuesta usando Playwright"""
        # Crear ticket para el usuario
        ticket = Ticket.objects.create(
            quantity=1,
            type='GENERAL',
            event=self.event,
            user=self.user
        )
        
        # Login del usuario usando el método helper
        self.login_user('testuser', 'testpass123')
        
        # Navegar a la encuesta de satisfacción (URL real)
        self.page.goto(f"{self.live_server_url}/tickets/{ticket.pk}/survey/")
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
        survey = SatisfactionSurvey.objects.get(ticket=ticket)
        self.assertEqual(survey.overall_satisfaction, 5)
        self.assertEqual(survey.purchase_experience, 'facil')
        self.assertTrue(survey.would_recommend)
        self.assertIn('Excelente', survey.comments or '')

    def test_satisfaction_survey_form_validation_errors(self):
        """Test validación de errores en el formulario usando Playwright"""
        # Crear ticket para el usuario
        ticket = Ticket.objects.create(
            quantity=1,
            type='VIP',
            event=self.event,
            user=self.user
        )
        
        # Login del usuario
        self.login_user('testuser', 'testpass123')
        
        # Navegar a la encuesta
        self.page.goto(f"{self.live_server_url}/tickets/{ticket.pk}/survey/")
        self.page.wait_for_load_state("networkidle")
        
        # Intentar enviar formulario sin completar campos requeridos
        self.page.click("button[type='submit']:has-text('Enviar encuesta')")
        
        # Verificar que aparecen mensajes de error o validación HTML5
        # En caso de validación HTML5, la página no se enviará
        expect(self.page).to_have_url(re.compile(f".*tickets/{ticket.pk}/survey.*"))

    def test_satisfaction_survey_ticket_information_display(self):
        """Test que verifica la información del ticket en la encuesta"""
        # Crear ticket VIP con múltiples entradas
        ticket = Ticket.objects.create(
            quantity=3,
            type='VIP',
            event=self.event,
            user=self.user
        )
        
        # Login del usuario
        self.login_user('testuser', 'testpass123')
        
        # Navegar a la encuesta
        self.page.goto(f"{self.live_server_url}/tickets/{ticket.pk}/survey/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar información del evento y ticket
        expect(self.page.locator("strong").filter(has_text="Test Event")).to_be_visible()
        expect(self.page.locator("p").filter(has_text="3 entrada")).to_be_visible()
        expect(self.page.locator("p").filter(has_text="Tipo: VIP")).to_be_visible()

    def test_satisfaction_survey_form_elements_present(self):
        """Test que verifica que todos los elementos del formulario están presentes"""
        # Crear ticket para el usuario
        ticket = Ticket.objects.create(
            quantity=1,
            type='GENERAL',
            event=self.event,
            user=self.user
        )
        
        # Login del usuario
        self.login_user('testuser', 'testpass123')
        
        # Navegar a la encuesta
        self.page.goto(f"{self.live_server_url}/tickets/{ticket.pk}/survey/")
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
        # Crear ticket para el usuario
        ticket = Ticket.objects.create(
            quantity=1,
            type='GENERAL',
            event=self.event,
            user=self.user
        )
        
        # Login del usuario
        self.login_user('testuser', 'testpass123')
        
        # Navegar a la encuesta
        self.page.goto(f"{self.live_server_url}/tickets/{ticket.pk}/survey/")
        self.page.wait_for_load_state("networkidle")
        
        # Probar en viewport móvil
        self.page.set_viewport_size({"width": 375, "height": 667})
        
        # Verificar que los elementos se adaptan al móvil
        expect(self.page.locator(".container")).to_be_visible()
        expect(self.page.locator("input[name='overall_satisfaction']").first).to_be_visible()
        expect(self.page.locator("button[type='submit']:has-text('Enviar encuesta')")).to_be_visible()
        
        # Probar en viewport desktop
        self.page.set_viewport_size({"width": 1200, "height": 800})
        
        # Verificar que sigue funcionando en desktop
        expect(self.page.locator("input[name='overall_satisfaction']").first).to_be_visible()
        expect(self.page.locator("button[type='submit']:has-text('Enviar encuesta')")).to_be_visible()

    def test_satisfaction_survey_complete_form_interaction(self):
        """Test interacción completa con todos los elementos del formulario"""
        # Crear ticket para el usuario
        ticket = Ticket.objects.create(
            quantity=2,
            type='VIP',
            event=self.event,
            user=self.user
        )
        
        # Login del usuario
        self.login_user('testuser', 'testpass123')
        
        # Navegar a la encuesta
        self.page.goto(f"{self.live_server_url}/tickets/{ticket.pk}/survey/")
        self.page.wait_for_load_state("networkidle")
        
        # Probar selecciones en cada campo
        satisfaction_radio = self.page.locator("input[name='overall_satisfaction'][value='3']")
        expect(satisfaction_radio).to_be_visible()
        satisfaction_radio.check()
        
        experience_select = self.page.locator("select[name='purchase_experience']")
        expect(experience_select).to_be_visible()
        experience_select.select_option("normal")
        
        recommend_radio = self.page.locator("input[name='would_recommend'][value='yes']")
        expect(recommend_radio).to_be_visible()
        recommend_radio.check()
        
        # Llenar textarea con comentarios largos
        comments_textarea = self.page.locator("textarea[name='comments']")
        expect(comments_textarea).to_be_visible()
        long_comment = "Este es un comentario más largo para probar que el textarea funciona correctamente con texto extenso y múltiples líneas."
        comments_textarea.fill(long_comment)
        
        # Verificar que el texto se ingresó correctamente
        expect(comments_textarea).to_have_value(long_comment)
        
        # Enviar formulario
        submit_button = self.page.locator("button[type='submit']:has-text('Enviar encuesta')")
        expect(submit_button).to_be_visible()
        submit_button.click()
        
        # Verificar redirección exitosa
        self.page.wait_for_url(re.compile(r".*(tickets|events).*"), timeout=10000)
        
        # Verificar datos en la base de datos
        survey = SatisfactionSurvey.objects.get(ticket=ticket)
        self.assertEqual(survey.overall_satisfaction, 3)
        self.assertEqual(survey.purchase_experience, 'normal')
        self.assertTrue(survey.would_recommend)
        self.assertEqual(survey.comments, long_comment)

    def test_satisfaction_survey_navigation_elements(self):
        """Test elementos de navegación en la página de encuesta"""
        # Crear ticket para el usuario
        ticket = Ticket.objects.create(
            quantity=1,
            type='GENERAL',
            event=self.event,
            user=self.user
        )
        
        # Login del usuario
        self.login_user('testuser', 'testpass123')
        
        # Navegar a la encuesta
        self.page.goto(f"{self.live_server_url}/tickets/{ticket.pk}/survey/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar elementos de navegación de Bootstrap
        expect(self.page.locator(".card").first).to_be_visible()  # Card container
        expect(self.page.locator(".card-header").first).to_be_visible()  # Card header
        expect(self.page.locator("text=EventHub")).to_be_visible()  # Brand name
        
        # Verificar que puede navegar usando el botón "Omitir encuesta"
        skip_button = self.page.locator("a.btn:has-text('Omitir encuesta')")
        expect(skip_button).to_be_visible()
        skip_button.click()
        self.page.wait_for_url(re.compile(r".*/tickets.*"), timeout=10000)
        expect(self.page).to_have_url(re.compile(r".*/tickets.*"))

    def test_satisfaction_survey_ticket_details_section(self):
        """Test que verifica la sección de detalles del ticket"""
        # Crear ticket para el usuario
        ticket = Ticket.objects.create(
            quantity=2,
            type='VIP',
            event=self.event,
            user=self.user
        )
        
        # Login del usuario
        self.login_user('testuser', 'testpass123')
        
        # Navegar a la encuesta
        self.page.goto(f"{self.live_server_url}/tickets/{ticket.pk}/survey/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar sección de detalles del ticket
        expect(self.page.locator("text=Detalles de tu compra")).to_be_visible()
        expect(self.page.locator("strong").filter(has_text="Test Event")).to_be_visible()
        expect(self.page.locator("text=Test Venue")).to_be_visible()
        expect(self.page.locator("p").filter(has_text="2 entrada")).to_be_visible()
        expect(self.page.locator(f"text={ticket.ticket_code}")).to_be_visible()

    def test_satisfaction_survey_success_purchase_message(self):
        """Test que verifica el mensaje de compra exitosa"""
        # Crear ticket para el usuario
        ticket = Ticket.objects.create(
            quantity=1,
            type='GENERAL',
            event=self.event,
            user=self.user
        )
        
        # Login del usuario
        self.login_user('testuser', 'testpass123')
        
        # Navegar a la encuesta
        self.page.goto(f"{self.live_server_url}/tickets/{ticket.pk}/survey/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar mensaje de compra exitosa
        expect(self.page.locator(".alert-success")).to_be_visible()
        expect(self.page.locator("text=¡Compra exitosa!")).to_be_visible()
        expect(self.page.locator("text=Has adquirido")).to_be_visible() 