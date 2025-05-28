import datetime
from django.utils import timezone
from playwright.sync_api import expect
from app.models import Event, User, Venue, Category, Coupon
from app.test.test_e2e.base import BaseE2ETest
from django.urls import reverse

expiration = (timezone.now() + datetime.timedelta(days=5)).replace(second=0, microsecond=0)

def assert_input_value_equals(locator, expected_value: str):
    actual_value = locator.input_value().replace(",", ".")
    assert actual_value == expected_value, f"Expected '{expected_value}', got '{actual_value}'"


class CouponBaseTest(BaseE2ETest):
    """Clase base específica para tests de cupones"""

    def setUp(self):
        super().setUp()

        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )

        self.regular_user = User.objects.create_user(
            username="usuario",
            email="usuario@example.com",
            password="password123",
            is_organizer=False,
        )

        self.venue= Venue.objects.create(
            name="Auditorio Nacional",
            address="60 y 124",
            capacity=5000,
            country="ARG",  
            city="La Plata"
        )

        self.category = Category.objects.create(name="Conferencia")

        event_date1 = timezone.make_aware(datetime.datetime(2025, 2, 10, 10, 10))
        self.event1 = Event.objects.create(
            title="Evento de prueba 1",
            description="Descripción del evento 1",
            scheduled_at=event_date1,
            organizer=self.organizer,
            venue=self.venue,
            price=50.00
        )
        self.event1.categories.add(self.category) 
        
        self.coupon = Coupon.objects.create(
            event=self.event1,
            discount_percent=20,
            expiration_date=expiration,
            organizer=self.organizer
        )



    def test_template_muestra_cupones(self):
        
        self.client.login(username='organizador', password='password123')
        url = reverse('coupon_list', args=[self.event1.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/coupons/coupon_list.html')

        self.assertContains(response, f'Cupones para "{self.event1.title}"')

        
        self.assertContains(response, self.coupon.code)
        self.assertContains(response, 'Crear Cupón')

        

    def test_navegacion_a_crear_cupon(self):
        self.client.login(username='organizador', password='password123')
        url_create = reverse('coupon_form', args=[self.event1.id])
        response = self.client.get(url_create)
    
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/coupons/coupon_form.html')
    
        
        self.assertContains(response, 'Porcentaje de Descuento *')
        self.assertContains(response, 'Fecha de Expiración *')
        
    def test_crear_cupon(self):
        expiration_str = expiration.strftime("%Y-%m-%dT%H:%M")
        self.client.login(username='organizador', password='password123')
        url_create = reverse('coupon_form', args=[self.event1.id])

        data = {
            'discount_percentage': '15',
            'expiration_date': expiration_str,
        }

        response = self.client.post(url_create, data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('coupon_list', args=[self.event1.id]))

        nuevo_cupon = Coupon.objects.filter(event=self.event1, discount_percent=15).first()
        self.assertIsNotNone(nuevo_cupon)

