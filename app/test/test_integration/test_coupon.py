from django.test import TestCase, Client
from django.urls import reverse
from app.models import User, Coupon

class CouponValidationViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='cliente', password='123456')
        self.client.login(username='cliente', password='123456')

    def test_valid_coupon_response(self):
        Coupon.objects.create(
            coupon_code="PROMO20",
            discount_type="fixed",
            amount=20,
            active=True
        )
        response = self.client.get(reverse('validate_coupon'), {'code': 'PROMO20'})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'valid': True,
            'message': '',
            'coupon': {'discount_type': 'fixed', 'amount': 20.0}
        })

    def test_invalid_coupon_response(self):
        response = self.client.get(reverse('validate_coupon'), {'code': 'NOEXISTE'})
        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertFalse(json['valid'])
        self.assertIn('Cupón no válido', json['message'])


