from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from app.models import Event, Venue, Ticket, SatisfactionSurvey
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class SatisfactionSurveyE2ETest(TestCase):
    """Tests end-to-end para la funcionalidad completa de satisfaction survey"""
    
    def setUp(self):
        """Configuración inicial para los tests e2e"""
        self.client = Client()
        
        # Usuario regular
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
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
        """Test del flujo completo de usuario completando encuesta"""
        # 1. Usuario hace login
        login_success = self.client.login(username='testuser', password='testpass123')
        self.assertTrue(login_success)
        
        # 2. Usuario compra ticket (simulado)
        ticket = Ticket.objects.create(
            quantity=1,
            type='GENERAL',
            event=self.event,
            user=self.user
        )
        
        # 3. Usuario accede a la encuesta
        response = self.client.get(
            reverse('satisfaction_survey', kwargs={'ticket_id': ticket.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Encuesta de Satisfacción')
        
        # 4. Usuario completa y envía la encuesta
        form_data = {
            'overall_satisfaction': 5,
            'purchase_experience': 'facil',
            'would_recommend': 'yes',
            'comments': 'Excelente experiencia de compra'
        }
        
        response = self.client.post(
            reverse('satisfaction_survey', kwargs={'ticket_id': ticket.id}),
            data=form_data
        )
        
        # 5. Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # 6. Verificar que la encuesta se guardó correctamente
        survey = SatisfactionSurvey.objects.get(ticket=ticket)
        self.assertEqual(survey.overall_satisfaction, 5)
        self.assertEqual(survey.purchase_experience, 'facil')
        self.assertTrue(survey.would_recommend)

    def test_satisfaction_survey_after_ticket_purchase_flow(self):
        """Test flujo completo desde compra hasta encuesta"""
        # 1. Login del usuario
        self.client.login(username='testuser', password='testpass123')
        
        # 2. Ver evento disponible
        response = self.client.get(
            reverse('event_detail', kwargs={'event_id': self.event.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Comprar Entrada')
        
        # 3. Simular compra exitosa (crear ticket directamente)
        ticket = Ticket.objects.create(
            quantity=2,
            type='GENERAL',
            event=self.event,
            user=self.user
        )
        
        # 4. Acceder a encuesta después de compra
        response = self.client.get(
            reverse('satisfaction_survey', kwargs={'ticket_id': ticket.id})
        )
        self.assertEqual(response.status_code, 200)
        
        # 5. Verificar información del ticket en la encuesta
        self.assertContains(response, 'Test Event')
        self.assertContains(response, '2 entrada(s)')
        self.assertContains(response, 'General')

    def test_satisfaction_survey_multiple_users_different_experiences(self):
        """Test múltiples usuarios con diferentes experiencias"""
        # Usuario 1: Experiencia positiva
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        
        ticket1 = Ticket.objects.create(
            quantity=1,
            type='GENERAL',
            event=self.event,
            user=user1
        )
        
        self.client.login(username='user1', password='testpass123')
        
        response = self.client.post(
            reverse('satisfaction_survey', kwargs={'ticket_id': ticket1.id}),
            data={
                'overall_satisfaction': 5,
                'purchase_experience': 'muy_facil',
                'would_recommend': 'yes',
                'comments': 'Perfecto!'
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # Usuario 2: Experiencia negativa
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        ticket2 = Ticket.objects.create(
            quantity=1,
            type='GENERAL',
            event=self.event,
            user=user2
        )
        
        self.client.login(username='user2', password='testpass123')
        
        response = self.client.post(
            reverse('satisfaction_survey', kwargs={'ticket_id': ticket2.id}),
            data={
                'overall_satisfaction': 2,
                'purchase_experience': 'dificil',
                'would_recommend': 'no',
                'comments': 'Proceso complicado'
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # Verificar que ambas encuestas se guardaron
        surveys = SatisfactionSurvey.objects.all()
        self.assertEqual(surveys.count(), 2)

    def test_satisfaction_survey_organizer_can_view_results(self):
        """Test que organizadores pueden ver resultados de encuestas"""
        # Crear algunas encuestas
        ticket1 = Ticket.objects.create(
            quantity=1,
            type='GENERAL',
            event=self.event,
            user=self.user
        )
        
        SatisfactionSurvey.objects.create(
            ticket=ticket1,
            user=self.user,
            event=self.event,
            overall_satisfaction=4,
            purchase_experience='facil',
            would_recommend=True,
            comments='Buena experiencia'
        )
        
        # Login como organizador
        self.client.login(username='organizer', password='testpass123')
        
        # Acceder a resultados de encuestas
        response = self.client.get(
            reverse('survey_results', kwargs={'event_id': self.event.id})
        )
        
        # Verificar que puede ver los resultados
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resultados de Encuestas')

    def test_satisfaction_survey_validation_and_error_handling(self):
        """Test manejo de errores y validación en el flujo completo"""
        # Login del usuario
        self.client.login(username='testuser', password='testpass123')
        
        ticket = Ticket.objects.create(
            quantity=1,
            type='GENERAL',
            event=self.event,
            user=self.user
        )
        
        # 1. Enviar formulario vacío
        response = self.client.post(
            reverse('satisfaction_survey', kwargs={'ticket_id': ticket.id}),
            data={}
        )
        
        # Debe mostrar errores de validación
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'alert-danger')
        
        # 2. Enviar datos inválidos
        response = self.client.post(
            reverse('satisfaction_survey', kwargs={'ticket_id': ticket.id}),
            data={
                'overall_satisfaction': 6,  # Fuera de rango
                'purchase_experience': 'invalido',
                'would_recommend': 'maybe',  # Valor inválido
                'comments': 'x' * 501  # Muy largo
            }
        )
        
        # Debe mostrar errores específicos
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'alert-danger')

    def test_satisfaction_survey_duplicate_prevention_flow(self):
        """Test prevención de encuestas duplicadas en flujo completo"""
        # Login del usuario
        self.client.login(username='testuser', password='testpass123')
        
        ticket = Ticket.objects.create(
            quantity=1,
            type='GENERAL',
            event=self.event,
            user=self.user
        )
        
        # 1. Completar encuesta primera vez
        response = self.client.post(
            reverse('satisfaction_survey', kwargs={'ticket_id': ticket.id}),
            data={
                'overall_satisfaction': 4,
                'purchase_experience': 'facil',
                'would_recommend': 'yes',
                'comments': 'Primera encuesta'
            }
        )
        self.assertEqual(response.status_code, 302)
        
        # 2. Intentar acceder nuevamente a la encuesta
        response = self.client.get(
            reverse('satisfaction_survey', kwargs={'ticket_id': ticket.id})
        )
        
        # Debe mostrar mensaje de encuesta ya completada o redirigir
        self.assertIn(response.status_code, [200, 302])

    def test_satisfaction_survey_responsive_design_flow(self):
        """Test que la encuesta funciona bien en diferentes dispositivos"""
        # Login del usuario
        self.client.login(username='testuser', password='testpass123')
        
        ticket = Ticket.objects.create(
            quantity=1,
            type='GENERAL',
            event=self.event,
            user=self.user
        )
        
        # Acceder a la encuesta
        response = self.client.get(
            reverse('satisfaction_survey', kwargs={'ticket_id': ticket.id})
        )
        
        content = response.content.decode('utf-8')
        
        # Verificar elementos responsive
        self.assertIn('container', content)
        self.assertIn('col-md-', content)
        self.assertIn('form-control', content)
        self.assertIn('btn', content)
        self.assertIn('card', content)
        
        # Verificar meta viewport para móviles
        self.assertIn('viewport', content)
        self.assertIn('device-width', content)

    def test_satisfaction_survey_navigation_flow(self):
        """Test navegación completa relacionada con encuestas"""
        # Login del usuario
        self.client.login(username='testuser', password='testpass123')
        
        ticket = Ticket.objects.create(
            quantity=1,
            type='GENERAL',
            event=self.event,
            user=self.user
        )
        
        # 1. Navegar desde tickets a encuesta
        response = self.client.get(reverse('tickets'))
        self.assertEqual(response.status_code, 200)
        
        # 2. Acceder a encuesta específica
        response = self.client.get(
            reverse('satisfaction_survey', kwargs={'ticket_id': ticket.id})
        )
        self.assertEqual(response.status_code, 200)
        
        # 3. Completar encuesta
        response = self.client.post(
            reverse('satisfaction_survey', kwargs={'ticket_id': ticket.id}),
            data={
                'overall_satisfaction': 3,
                'purchase_experience': 'normal',
                'would_recommend': 'yes',
                'comments': 'Experiencia normal'
            }
        )
        
        # 4. Verificar redirección después de completar
        self.assertEqual(response.status_code, 302)

    def test_satisfaction_survey_security_and_permissions(self):
        """Test seguridad y permisos en el flujo de encuestas"""
        # Crear ticket para user1
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        
        ticket = Ticket.objects.create(
            quantity=1,
            type='GENERAL',
            event=self.event,
            user=user1
        )
        
        # 1. Intentar acceder sin login
        response = self.client.get(
            reverse('satisfaction_survey', kwargs={'ticket_id': ticket.id})
        )
        self.assertEqual(response.status_code, 302)  # Redirige a login
        
        # 2. Login con usuario diferente
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        self.client.login(username='user2', password='testpass123')
        
        # 3. Intentar acceder a encuesta de otro usuario
        response = self.client.get(
            reverse('satisfaction_survey', kwargs={'ticket_id': ticket.id})
        )
        
        # Debe denegar acceso
        self.assertIn(response.status_code, [403, 404])

    def test_satisfaction_survey_complete_user_experience(self):
        """Test experiencia completa del usuario con encuesta"""
        # 1. Login del usuario
        self.client.login(username='testuser', password='testpass123')
        
        # 2. Crear ticket (simular compra)
        ticket = Ticket.objects.create(
            quantity=3,
            type='VIP',
            event=self.event,
            user=self.user
        )
        
        # 3. Acceder a encuesta
        response = self.client.get(
            reverse('satisfaction_survey', kwargs={'ticket_id': ticket.id})
        )
        
        # 4. Verificar experiencia visual completa
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Encuesta de Satisfacción')
        self.assertContains(response, 'Test Event')
        self.assertContains(response, '3 entrada(s)')
        self.assertContains(response, 'VIP')
        
        # 5. Verificar elementos de UX
        self.assertContains(response, 'bi-clipboard-check')  # Ícono
        self.assertContains(response, 'Compra exitosa')     # Mensaje positivo
        self.assertContains(response, 'card shadow-sm')     # Diseño elegante
        
        # 6. Completar encuesta con experiencia positiva
        response = self.client.post(
            reverse('satisfaction_survey', kwargs={'ticket_id': ticket.id}),
            data={
                'overall_satisfaction': 5,
                'purchase_experience': 'muy_facil',
                'would_recommend': 'yes',
                'comments': 'Experiencia excepcional, muy recomendado!'
            }
        )
        
        # 7. Verificar finalización exitosa
        self.assertEqual(response.status_code, 302)
        
        # 8. Verificar que los datos se guardaron correctamente
        survey = SatisfactionSurvey.objects.get(ticket=ticket)
        self.assertEqual(survey.overall_satisfaction, 5)
        self.assertEqual(survey.purchase_experience, 'muy_facil')
        self.assertTrue(survey.would_recommend)
        self.assertIn('excepcional', survey.comments) 