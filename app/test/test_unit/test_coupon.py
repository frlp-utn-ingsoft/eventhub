from django.test import TestCase
from decimal import Decimal
from app.models import Ticket, Coupon, User, Event
from django.utils.timezone import now, timedelta

class CouponModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='123')
        self.event = Event.objects.create(
            title="Evento Test",
            description="Descripción",
            scheduled_at=now() + timedelta(days=1),
            organizer=self.user,
            price_general=Decimal('100.00'),
            price_vip=Decimal('200.00'),
            tickets_total=100
        )

    def test_ticket_with_fixed_coupon(self):
        coupon = Coupon.objects.create(
            coupon_code="FIJO10",
            discount_type="fixed",
            amount=Decimal('10.00'),
            active=True
        )
        ticket = Ticket.objects.create(
            user=self.user,
            event=self.event,
            quantity=1,
            type='general',
            card_type='credit',
            coupon=coupon
        )
        self.assertEqual(ticket.discount_amount, Decimal('10.00'))
        self.assertEqual(ticket.total, Decimal('110.00') - Decimal('10.00'))

    def test_ticket_with_percent_coupon(self):
        coupon = Coupon.objects.create(
            coupon_code="DESC25",
            discount_type="percent",
            amount=Decimal('25.00'),
            active=True
        )
        ticket = Ticket.objects.create(
            user=self.user,
            event=self.event,
            quantity=1,
            type='general',
            card_type='debit',
            coupon=coupon
        )
        expected_discount = (Decimal('100.00') + Decimal('10.00')) * Decimal('0.25')
        expected_total = (Decimal('100.00') + Decimal('10.00')) - expected_discount
        self.assertAlmostEqual(ticket.total, expected_total, places=2)

