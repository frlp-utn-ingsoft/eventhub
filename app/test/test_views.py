from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

class RefundRequestViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="user", password="pass")
        self.client.login(username="user", password="pass")

    def test_refund_form_view_get(self):
        response = self.client.get(reverse("refund_form"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/refund_form.html")

    def test_refund_form_post_valid(self):
        response = self.client.post(reverse("refund_form"), {
            "ticket_code": "123",
            "reason": "event_cancelled",
            "additional_details": "No puedo ir",
            "accepted_policy": "on"
        })
        self.assertEqual(response.status_code, 302)  # Redirección

