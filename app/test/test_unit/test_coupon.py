import datetime
import string
from django.test import TestCase
from django.utils import timezone
from app.models import Event, User, Venue, Coupon

class CouponModelTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador_coupon",
            email="coupon_organizer@example.com",
            password="password123",
            is_organizer=True,
        )

        self.venue = Venue.objects.create(
            name="Centro de Convenciones",
            address="Av. Siempre Viva 742",
            capacity=1000,
            country="ARG",
            city="Buenos Aires"
        )

        self.event = Event.objects.create(
            title="Festival de Música",
            description="Un festival con muchas bandas",
            scheduled_at=timezone.now() + datetime.timedelta(days=10),
            organizer=self.organizer,
            venue=self.venue,
            price=5000.00
        )

    def test_coupon_creation(self):
        """Test que verifica la creación de un cupón con datos válidos"""
        expiration = timezone.now() + datetime.timedelta(days=5)

        coupon = Coupon.objects.create(
            event=self.event,
            discount_percent=20,
            expiration_date=expiration,
            organizer=self.organizer
        )

        self.assertTrue(coupon.code)
        self.assertEqual(len(coupon.code), 8)
        self.assertTrue(coupon.code.isalnum())
        self.assertTrue(coupon.active)
        self.assertEqual(coupon.discount_percent, 20)
        self.assertEqual(coupon.event, self.event)
        self.assertEqual(coupon.organizer, self.organizer)
        self.assertEqual(coupon.expiration_date, expiration)


    def test_coupon_str_representation(self):
        """Test que verifica el formato del método __str__ del cupón"""
        coupon = Coupon.objects.create(
            event=self.event,
            discount_percent=15,
            expiration_date=timezone.now() + datetime.timedelta(days=3),
            organizer=self.organizer
        )

        expected_str = f"{coupon.code} - 15% - Evento: {self.event.title}"
        self.assertEqual(str(coupon), expected_str)


        coupon.active = False
        coupon.save()

        coupon_refreshed = Coupon.objects.get(pk=coupon.pk)
        self.assertFalse(coupon_refreshed.active)