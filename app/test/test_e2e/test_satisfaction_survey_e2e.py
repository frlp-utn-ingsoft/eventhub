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
        
        # Navegar a la encuesta de satisfacción
        self.page.goto(f"{self.live_server_url}/satisfaction-survey/{ticket.id}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que la página de encuesta cargó correctamente
        expect(self.page.locator("h1")).to_contain_text("Encuesta de Satisfacción")
        expect(self.page.locator("text=Test Event")).to_be_visible()
        
        # Verificar que los elementos del formulario están presentes
        expect(self.page.locator("select#overall_satisfaction")).to_be_visible()
        expect(self.page.locator("select#purchase_experience")).to_be_visible()
        expect(self.page.locator("select#would_recommend")).to_be_visible()
        expect(self.page.locator("textarea#comments")).to_be_visible()
        
        # Llenar el formulario de encuesta
        self.page.select_option("select#overall_satisfaction", "5")
        self.page.select_option("select#purchase_experience", "facil")
        self.page.select_option("select#would_recommend", "yes")
        self.page.fill("textarea#comments", "Excelente experiencia de compra!")
        
        # Enviar el formulario
        self.page.click("button[type='submit']")
        
        # Verificar redirección exitosa (puede ser a tickets o eventos)
        self.page.wait_for_url(re.compile(r".*(tickets|events).*"), timeout=10000)
        
        # Verificar que la encuesta se guardó en la base de datos
        survey = SatisfactionSurvey.objects.get(ticket=ticket)
        self.assertEqual(survey.overall_satisfaction, 5)
        self.assertEqual(survey.purchase_experience, 'facil')
        self.assertTrue(survey.would_recommend)
        self.assertIn('Excelente', survey.comments)

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
        self.page.goto(f"{self.live_server_url}/satisfaction-survey/{ticket.id}/")
        self.page.wait_for_load_state("networkidle")
        
        # Intentar enviar formulario vacío
        self.page.click("button[type='submit']")
        
        # Verificar que aparecen mensajes de error
        expect(self.page.locator(".alert-danger")).to_be_visible()
        
        # Verificar que seguimos en la misma página
        expect(self.page).to_have_url(re.compile(f".*satisfaction-survey/{ticket.id}/"))

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
        self.page.goto(f"{self.live_server_url}/satisfaction-survey/{ticket.id}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar información del evento y ticket
        expect(self.page.locator("text=Test Event")).to_be_visible()
        expect(self.page.locator("text=3 entrada")).to_be_visible()
        expect(self.page.locator("text=VIP")).to_be_visible()

    def test_satisfaction_survey_duplicate_prevention(self):
        """Test prevención de encuestas duplicadas usando Playwright"""
        # Crear ticket y encuesta existente
        ticket = Ticket.objects.create(
            quantity=1,
            type='GENERAL',
            event=self.event,
            user=self.user
        )
        
        SatisfactionSurvey.objects.create(
            ticket=ticket,
            user=self.user,
            event=self.event,
            overall_satisfaction=4,
            purchase_experience='facil',
            would_recommend=True
        )
        
        # Login del usuario
        self.login_user('testuser', 'testpass123')
        
        # Intentar acceder nuevamente a la encuesta
        self.page.goto(f"{self.live_server_url}/satisfaction-survey/{ticket.id}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que muestra mensaje de encuesta ya completada o redirige
        if self.page.url == f"{self.live_server_url}/satisfaction-survey/{ticket.id}/":
            expect(self.page.locator("text=ya has completado")).to_be_visible()
        else:
            # Si redirigió, verificar que no estamos en la página de encuesta
            expect(self.page).not_to_have_url(re.compile(f".*satisfaction-survey/{ticket.id}/"))

    def test_satisfaction_survey_unauthorized_access(self):
        """Test acceso no autorizado a encuesta de otro usuario"""
        # Crear otro usuario y su ticket
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        ticket = Ticket.objects.create(
            quantity=1,
            type='GENERAL',
            event=self.event,
            user=other_user
        )
        
        # Login con el usuario original (no el dueño del ticket)
        self.login_user('testuser', 'testpass123')
        
        # Intentar acceder a encuesta de otro usuario
        self.page.goto(f"{self.live_server_url}/satisfaction-survey/{ticket.id}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar que se deniega el acceso (404 o 403, o redirige)
        if "satisfaction-survey" in self.page.url:
            expect(self.page.locator("text=403")).to_be_visible()
        else:
            # Si redirigió, está bien
            expect(self.page).not_to_have_url(re.compile(f".*satisfaction-survey/{ticket.id}/"))

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
        self.page.goto(f"{self.live_server_url}/satisfaction-survey/{ticket.id}/")
        self.page.wait_for_load_state("networkidle")
        
        # Probar en viewport móvil
        self.page.set_viewport_size({"width": 375, "height": 667})
        
        # Verificar que los elementos se adaptan al móvil
        expect(self.page.locator(".container")).to_be_visible()
        expect(self.page.locator("select#overall_satisfaction")).to_be_visible()
        expect(self.page.locator("button[type='submit']")).to_be_visible()
        
        # Probar en viewport desktop
        self.page.set_viewport_size({"width": 1200, "height": 800})
        
        # Verificar que sigue funcionando en desktop
        expect(self.page.locator("select#overall_satisfaction")).to_be_visible()
        expect(self.page.locator("button[type='submit']")).to_be_visible()

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
        self.page.goto(f"{self.live_server_url}/satisfaction-survey/{ticket.id}/")
        self.page.wait_for_load_state("networkidle")
        
        # Probar diferentes selecciones en cada campo
        satisfaction_select = self.page.locator("select#overall_satisfaction")
        expect(satisfaction_select).to_be_visible()
        satisfaction_select.select_option("3")
        
        experience_select = self.page.locator("select#purchase_experience")
        expect(experience_select).to_be_visible()
        experience_select.select_option("normal")
        
        recommend_select = self.page.locator("select#would_recommend")
        expect(recommend_select).to_be_visible()
        recommend_select.select_option("yes")
        
        # Llenar textarea con comentarios largos
        comments_textarea = self.page.locator("textarea#comments")
        expect(comments_textarea).to_be_visible()
        long_comment = "Este es un comentario más largo para probar que el textarea funciona correctamente con texto extenso y múltiples líneas."
        comments_textarea.fill(long_comment)
        
        # Verificar que el texto se ingresó correctamente
        expect(comments_textarea).to_have_value(long_comment)
        
        # Enviar formulario
        submit_button = self.page.locator("button[type='submit']")
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
        self.page.goto(f"{self.live_server_url}/satisfaction-survey/{ticket.id}/")
        self.page.wait_for_load_state("networkidle")
        
        # Verificar elementos de navegación
        expect(self.page.locator("nav")).to_be_visible()  # Navbar
        expect(self.page.locator("text=EventHub")).to_be_visible()  # Logo o nombre
        expect(self.page.locator("text=Eventos")).to_be_visible()  # Link a eventos
        
        # Verificar que puede navegar de vuelta a eventos
        self.page.click("text=Eventos")
        self.page.wait_for_url(re.compile(r".*/events.*"), timeout=10000)
        expect(self.page).to_have_url(re.compile(r".*/events.*")) 