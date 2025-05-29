from django.test import TestCase
from app.models import Discount

class DiscountModelTest(TestCase):    
    def test_discount_creation(self):
        discount = Discount.objects.create(
            code="UTN-FRLP",
            multiplier=0.8
        )

        """
        Test que verifica la creación correcta de descuentos
        """
        self.assertEqual(discount.code, "UTN-FRLP")
        self.assertEqual(discount.multiplier, 0.8)
        self.assertIsNotNone(discount.code)

    def test_discount_validate_with_valid_data(self):
        """
        Test que verifica la validación de descuentos con datos válidos
        """

        errors = Discount.validate(
            code="LA-PLATA",
            multiplier=0.9
        )
        
        self.assertEqual(errors, {})
