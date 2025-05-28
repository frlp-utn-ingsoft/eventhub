import datetime
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from app.models import Event, User, Venue, Coupon

expiration = (timezone.now() + datetime.timedelta(days=5)).replace(second=0, microsecond=0)


class BaseCouponTestCase(TestCase):
    
     def setUp(self):
        # Crear un usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )

        #Creacion de venue para los eventos
        self.venue = Venue.objects.create(
            name="Auditorio Nacional",
            address="60 y 124",
            capacity=5000,
            country="ARG",  
            city="La Plata"
            
        )
        
        # Crear un usuario regular
        self.regular_user = User.objects.create_user(
            username="regular",
            email="regular@test.com",
            password="password123",
            is_organizer=False,
        )

        self.event1 = Event.objects.create(
            title="Evento 1",
            description="Descripción del evento 1",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
            price=100.00
        )
        
        self.coupon1 = Coupon.objects.create(
            event=self.event1,
            discount_percent=20,
            expiration_date=expiration,
            organizer=self.organizer
        )

        self.client = Client()

class CouponListViewTest(BaseCouponTestCase):
    

    def test_events_view_with_organizer_login(self):
        """Test que verifica que la vista cupones funciona cuando el usuario es organizador"""
        # Login con usuario organizador
        self.client.login(username="organizador", password="password123")

        # Hacer petición a la vista cupons
        response = self.client.get(reverse("coupon_list", args=[self.event1.id]))


        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["user_is_organizer"])
        self.assertTemplateUsed(response, "app/coupons/coupon_list.html")

class CouponFormViewTest(BaseCouponTestCase):
    """Tests para la vista del formulario de cuponess"""

    def test_coupon_form_view_with_organizer(self):
        """Test que verifica que la vista coupon_form funciona cuando el usuario es organizador"""
        # Login con usuario organizador
        self.client.login(username="organizador", password="password123")

        # Hacer petición a la vista event_form para crear nuevo evento (id=None)
        response = self.client.get(reverse("coupon_form", args=[self.event1.id]))


        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/coupons/coupon_form.html")
        self.assertIn("event", response.context)
        self.assertTrue(response.context["user_is_organizer"])

    

    def test_coupon_form_edit_existing(self):
        """Test que verifica que se puede editar un cupon existente"""
        # Login con usuario organizador
        self.client.login(username="organizador", password="password123")

        # Hacer petición a la vista coupon_form para editar cupon existente
        response = self.client.get(reverse("coupon_edit", args=[self.event1.id, self.coupon1.id]))


        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/coupons/coupon_edit.html")
        self.assertEqual(response.context["coupon"].id, self.coupon1.id)
        self.assertEqual(response.context["event"].id, self.event1.id)



class CouponFormSubmissionTest(BaseCouponTestCase):
    """Tests para la creación y edición de cupones mediante POST"""

    def test_coupon_form_post_create(self):
        """Test que verifica que se puede crear un cupón mediante POST"""

     # Login con usuario organizador
        self.client.login(username="organizador", password="password123")

        # Crear datos para el cupón
        coupon_data = {
        "discount_percentage": 20,
        "expiration_date": expiration.strftime("%Y-%m-%dT%H:%M"),
     }

        # Hacer petición POST a la vista coupon_form, pasando el ID del evento
        response = self.client.post(reverse("coupon_form", args=[self.event1.id]), coupon_data)

        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)

        # Verificar redirección al listado de cupones (no a detalle de cupón)
        self.assertEqual(response.url, reverse("coupon_list", args=[self.event1.id]))

        # Verificar que se creó el cupón
        coupons = Coupon.objects.filter(event=self.event1, discount_percent=20)
        self.assertEqual(coupons.count(), 2)

        # Obtenemos el nuevo cupón creado
        coupon = coupons.exclude(id=self.coupon1.id).get()

        # Verificar los atributos del cupón
        self.assertEqual(coupon.discount_percent, 20)
        self.assertEqual(coupon.event, self.event1)
        self.assertEqual(coupon.organizer, self.organizer)
        self.assertEqual(
        coupon.expiration_date.replace(microsecond=0),
        expiration.replace(microsecond=0)
        )
        self.assertTrue(coupon.active)
        self.assertTrue(bool(coupon.code))


