from django.contrib import messages
from django.test import TestCase
from django.urls import reverse
import json

from app.models import User, Discount


class BaseDiscountTestCase(TestCase):
    """
    Clase base con la configuración común para todos los test de descuentos.
    """

    def setUp(self):
        # Crear un usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )

        # Crear un usuario regular
        self.regular_user = User.objects.create_user(
            username="regular",
            email="regular@test.com",
            password="password123",
            is_organizer=False,
        )

        # Crear un descuento
        self.discount = Discount.objects.create (
            code='UTN-FRLP',
            multiplier=0.8
        )

class DiscountViewTest(BaseDiscountTestCase):
    """
    Tests para la vista de validar códigos de dscuento.
    """
    def test_validate_discount(self):
        """
        Verifica que el código enviado sea válido.
        """
        # Login con usuario regular
        self.client.login(username="regular", password="password123")

        code = 'UTN-FRLP'
        
        response_post = self.client.post(
            reverse('is_valid_code'),
            data=json.dumps(code),
            content_type='application/json'
        )

        messages_list = list(messages.get_messages(response_post.wsgi_request))

        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), "Código validado correctamente")