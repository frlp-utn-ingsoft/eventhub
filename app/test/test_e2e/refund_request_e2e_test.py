from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from app.models import RefundRequest
from django.utils.timezone import now

User = get_user_model()

class RefundE2ETest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='gordo', password='123456')
        self.client.login(username='gordo', password='123456')


        RefundRequest.objects.create(
            user=self.user,
            ticket_code="33cf3697-81e5-420f-ac9a-2374e3fb1f61",
            reason='Solicitud pendiente',
            approved=None,
            created_at=now()
        )

    def test_no_permitir_crear_solicitud_si_hay_pendiente(self):
        response = self.client.post(
            reverse('create_refund'),
            data={
                'ticket_code': "33cf3697-81e5-420f-ac9a-2374e3fb1f62",
                'reason': 'Intento crear otra',
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya tienes una solicitud de reembolso pendiente")
        self.assertEqual(RefundRequest.objects.filter(user=self.user).count(), 1)
