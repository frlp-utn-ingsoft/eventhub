from django.test import TestCase, Client
from django.urls import reverse
from app.models import User, Event, Coupon, Ticket
from django.utils.timezone import now, timedelta
from decimal import Decimal

class PurchaseFlowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='comprador', password='clave123')
        self.event = Event.objects.create(
            title="Show Test",
            description="Descripción",
            scheduled_at=now() + timedelta(days=2),
            organizer=self.user,
            price_general=Decimal('100.00'),
            price_vip=Decimal('150.00'),
            tickets_total=10
        )
        self.coupon = Coupon.objects.create(
            coupon_code="DESC10",
            discount_type="fixed",
            amount=Decimal('10.00'),
            active=True
        )

    def test_buy_ticket_with_coupon(self):
        self.client.login(username='comprador', password='clave123')
        url = reverse('buy_ticket_from_event', args=[self.event.id])

        data = {
            'quantity': 1,
            'type': 'general',
            'card_type': 'credit',
            'card_number': '1234567890123456',
            'card_cvv': '123',
            'expiry_month': '12',
            'expiry_year': '30',
            'coupon_code': 'DESC10',
        }

        response = self.client.post(url, data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Ticket.objects.filter(user=self.user, event=self.event).exists())

        ticket = Ticket.objects.get(user=self.user, event=self.event)
        self.assertEqual(ticket.coupon, self.coupon)
        self.assertEqual(ticket.total, Decimal('110.00') - Decimal('10.00'))

