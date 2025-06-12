from django.test import TestCase
from django.utils import timezone

from app.models import Event, SurveyResponse, Ticket, User, Venue


class SurveyResponseModelTest(TestCase):
    def setUp(self):
        # Crear usuario
        self.user = User.objects.create_user(username="testuser", password="testpass", email="test@example.com")

        # Crear venue
        self.venue = Venue.objects.create(
            name="Test Venue",
            address="123 Calle",
            city="Ciudad Test",
            capacity=1000,
            contact="contacto@test.com"
        )

        # Crear evento
        self.event = Event.objects.create(
            title="Test Event",
            description="Este es un evento de prueba",
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            organizer=self.user,
            venue=self.venue,
            status="active"
        )

        # Crear ticket
        self.ticket = Ticket.objects.create(
            user=self.user,
            event=self.event,
            quantity=2,
            type="GENERAL"
        )

    def test_create_survey_response(self):
        # Crear survey response
        response = SurveyResponse.objects.create(
            ticket=self.ticket,
            satisfaction=4,
            issue="No hubo problemas",
            recommend=True
        )

        self.assertEqual(response.ticket, self.ticket)
        self.assertEqual(response.satisfaction, 4)
        self.assertEqual(response.issue, "No hubo problemas")
        self.assertTrue(response.recommend)
        self.assertIsNotNone(response.submitted_at)
