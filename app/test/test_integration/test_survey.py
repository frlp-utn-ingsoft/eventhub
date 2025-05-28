import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import Event, Ticket, User


class SurveyIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='viewer', password='12345')
        self.client.login(username='viewer', password='12345')

        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            scheduled_at=timezone.now() - datetime.timedelta(days=1),
            organizer=self.user
        )

        self.ticket = Ticket.objects.create(
            user=self.user,
            event=self.event,
            quantity=1  
        )

    def test_access_survey_form(self):
        url = reverse('satisfaction_survey', args=[self.ticket.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Encuesta')  # Ajustalo si tu template usa otro texto

    def test_submit_survey(self):
        url = reverse('satisfaction_survey', args=[self.ticket.id])
        response = self.client.post(url, {
            'rating': 5,
            'comment': 'Muy bueno'
        })
        self.assertEqual(response.status_code, 200)  # o 200 si no redirige
