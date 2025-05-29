from django.test import TestCase
from django.contrib.auth import get_user_model
from app.models import Event, Venue, Ticket, SatisfactionSurvey
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class SatisfactionSurveyUnitTest(TestCase):
    """Tests unitarios para la funcionalidad de satisfaction survey"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.organizer = User.objects.create_user(
            username='organizer',
            email='organizer@example.com',
            password='testpass123',
            is_organizer=True
        )
        
        self.venue = Venue.objects.create(
            name='Test Venue',
            adress='Test Address',
            city='Test City',
            capacity=100,
            contact='test@venue.com'
        )
        
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            scheduled_at=timezone.now() + timedelta(days=30),
            organizer=self.organizer,
            venue=self.venue
        )
        
        self.ticket = Ticket.objects.create(
            quantity=2,
            type='GENERAL',
            event=self.event,
            user=self.user
        )

    def test_satisfaction_survey_creation_success(self):
        """Test creación exitosa de encuesta de satisfacción"""
        success, survey = SatisfactionSurvey.new(
            ticket=self.ticket,
            user=self.user,
            event=self.event,
            overall_satisfaction=5,
            purchase_experience='facil',
            would_recommend=True,
            comments='Excelente experiencia'
        )
        
        self.assertTrue(success)
        self.assertIsInstance(survey, SatisfactionSurvey)
        self.assertEqual(survey.overall_satisfaction, 5)
        self.assertEqual(survey.purchase_experience, 'facil')
        self.assertTrue(survey.would_recommend)
        self.assertEqual(survey.comments, 'Excelente experiencia')

    def test_satisfaction_survey_validation_required_fields(self):
        """Test validación de campos requeridos"""
        success, errors = SatisfactionSurvey.new(
            ticket=self.ticket,
            user=self.user,
            event=self.event,
            overall_satisfaction=None,
            purchase_experience='',
            would_recommend=None,
            comments=''
        )
        
        self.assertFalse(success)
        self.assertIn('overall_satisfaction', errors)
        self.assertIn('purchase_experience', errors)
        self.assertIn('would_recommend', errors)

    def test_satisfaction_survey_validation_invalid_satisfaction(self):
        """Test validación de satisfacción inválida"""
        success, errors = SatisfactionSurvey.new(
            ticket=self.ticket,
            user=self.user,
            event=self.event,
            overall_satisfaction=6,  # Inválido (debe ser 1-5)
            purchase_experience='facil',
            would_recommend=True
        )
        
        self.assertFalse(success)
        self.assertIn('overall_satisfaction', errors)

    def test_satisfaction_survey_validation_invalid_experience(self):
        """Test validación de experiencia inválida"""
        success, errors = SatisfactionSurvey.new(
            ticket=self.ticket,
            user=self.user,
            event=self.event,
            overall_satisfaction=4,
            purchase_experience='invalido',  # Inválido
            would_recommend=True
        )
        
        self.assertFalse(success)
        self.assertIn('purchase_experience', errors)

    def test_satisfaction_survey_validation_long_comments(self):
        """Test validación de comentarios muy largos"""
        long_comment = 'x' * 501  # Más de 500 caracteres
        
        success, errors = SatisfactionSurvey.new(
            ticket=self.ticket,
            user=self.user,
            event=self.event,
            overall_satisfaction=4,
            purchase_experience='facil',
            would_recommend=True,
            comments=long_comment
        )
        
        self.assertFalse(success)
        self.assertIn('comments', errors)

    def test_satisfaction_survey_duplicate_prevention(self):
        """Test prevención de encuestas duplicadas"""
        # Crear primera encuesta
        SatisfactionSurvey.objects.create(
            ticket=self.ticket,
            user=self.user,
            event=self.event,
            overall_satisfaction=4,
            purchase_experience='facil',
            would_recommend=True
        )
        
        # Intentar crear segunda encuesta para el mismo ticket
        success, errors = SatisfactionSurvey.new(
            ticket=self.ticket,
            user=self.user,
            event=self.event,
            overall_satisfaction=5,
            purchase_experience='muy_facil',
            would_recommend=True
        )
        
        self.assertFalse(success)
        self.assertIn('ticket', errors)

    def test_satisfaction_survey_str_method(self):
        """Test método __str__ del modelo"""
        survey = SatisfactionSurvey.objects.create(
            ticket=self.ticket,
            user=self.user,
            event=self.event,
            overall_satisfaction=4,
            purchase_experience='facil',
            would_recommend=True
        )
        
        expected_str = f"Encuesta de {self.user.username} - {self.event.title}"
        self.assertEqual(str(survey), expected_str)

    def test_satisfaction_survey_get_satisfaction_display(self):
        """Test método para mostrar satisfacción con ícono"""
        survey = SatisfactionSurvey.objects.create(
            ticket=self.ticket,
            user=self.user,
            event=self.event,
            overall_satisfaction=5,
            purchase_experience='facil',
            would_recommend=True
        )
        
        display = survey.get_satisfaction_display_with_icon()
        self.assertIn('😁', display)
        self.assertIn('Muy satisfecho', display)

    def test_satisfaction_survey_model_fields(self):
        """Test que todos los campos del modelo funcionan correctamente"""
        survey = SatisfactionSurvey.objects.create(
            ticket=self.ticket,
            user=self.user,
            event=self.event,
            overall_satisfaction=3,
            purchase_experience='normal',
            would_recommend=False,
            comments='Comentario de prueba'
        )
        
        # Verificar que se guardó correctamente
        saved_survey = SatisfactionSurvey.objects.get(id=survey.id)
        self.assertEqual(saved_survey.overall_satisfaction, 3)
        self.assertEqual(saved_survey.purchase_experience, 'normal')
        self.assertFalse(saved_survey.would_recommend)
        self.assertEqual(saved_survey.comments, 'Comentario de prueba')

    def test_satisfaction_survey_relationships(self):
        """Test relaciones del modelo SatisfactionSurvey"""
        survey = SatisfactionSurvey.objects.create(
            ticket=self.ticket,
            user=self.user,
            event=self.event,
            overall_satisfaction=4,
            purchase_experience='facil',
            would_recommend=True
        )
        
        # Verificar relaciones
        self.assertEqual(survey.ticket, self.ticket)
        self.assertEqual(survey.user, self.user)
        self.assertEqual(survey.event, self.event)
        
        # Verificar relaciones inversas
        self.assertIn(survey, self.user.satisfaction_surveys.all())
        self.assertIn(survey, self.event.satisfaction_surveys.all()) 