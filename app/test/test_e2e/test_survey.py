from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import Event, SurveyResponse, Ticket

User = get_user_model()

class SatisfactionSurveyTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')

        self.event = Event.objects.create(
            title="Test Event",
            description="Descripción de prueba",
            scheduled_at=timezone.make_aware(datetime(2030, 1, 1, 10, 0)),
            organizer=self.user,
            status="active",
        )

        self.ticket = Ticket.objects.create(
            user=self.user,
            event=self.event,
            quantity=1,
            type="GENERAL"
        )

        self.client.login(username='testuser', password='password123')

    def test_get_survey_form(self):
        url = reverse("satisfaction_survey", args=[self.ticket.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")

    def test_post_valid_survey(self):
        url = reverse("satisfaction_survey", args=[self.ticket.id])
        data = {
            "satisfaction": 5,
            "recommend": True
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("ticket_list"))
        self.assertTrue(SurveyResponse.objects.filter(ticket=self.ticket).exists())

    def test_prevent_double_survey(self):
        SurveyResponse.objects.create(ticket=self.ticket, satisfaction=3, recommend=True)
        url = reverse("satisfaction_survey", args=[self.ticket.id])
        response = self.client.get(url)
        self.assertRedirects(response, reverse("ticket_list"))
