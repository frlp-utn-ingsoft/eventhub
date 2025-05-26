import datetime
from django.test import TestCase
from django.utils import timezone
from app.models import Ticket, User, Event, Venue

class TicketModelTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador_test",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )

        self.user = User.objects.create_user(
            username="normie_test",
            email="normie_test@example.com",
            password="password123",
            is_organizer=False,
        )

        self.venue = Venue.objects.create(
            name = "venue__name-test",
            adress = "venue__adress-test",
            city = "venue__city-test",
            capacity = 15000,
            contact = "venue__contac-test"
        )
        
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue= self.venue
        )
    
    def test_ticket_creation(self):
        ticket = Ticket.objects.create(
            quantity=1,
            type="VIP",
            event=self.event,
            user=self.user
        )

        """
        Test que verifica la creación correcta de tickets
        """
        self.assertEqual(ticket.quantity, 1)
        self.assertEqual(ticket.type, "VIP")
        self.assertEqual(ticket.user, self.user)
        self.assertEqual(ticket.event, self.event)
        self.assertIsNotNone(ticket.buy_date)
        self.assertIsNotNone(ticket.ticket_code)

    def test_ticket_validate_with_valid_data(self):
        """
        Test que verifica la validación de eventos con datos válidos
        """

        errors = Ticket.validate(
            quantity=1,
            type="VIP",
            event=self.event,
            user=self.user,
        )
        
        self.assertEqual(errors, {})
    
    def test_ticket_validate_with_empty_quantity(self):
        """
        Test que verifica la validación de tickets con cantidades vacías
        """

        errors = Ticket.validate(
            quantity=None,
            type="VIP",
            event=self.event,
            user=self.user,    
        )

        self.assertIn("quantity", errors)

        self.assertEqual(errors["quantity"], "La cantidad es requerida")

    def test_ticket_validate_with_negative_quantity(self):
        """
        Test que verifica la validación de tickets con cantidades negativas
        """

        errors = Ticket.validate(
            quantity=-1,
            type="VIP",
            event=self.event,
            user=self.user,    
        )

        self.assertIn("quantity", errors)

        self.assertEqual(errors["quantity"], "La cantidad debe ser al menos 1")
    
    def test_ticket_validate_with_non_integer_quantity(self):
        """
        Test que verifica la validación de tickets con cantidades no enteras
        """

        errors = Ticket.validate(
            quantity=1.4,
            type="VIP",
            event=self.event,
            user=self.user,    
        )

        self.assertIn("quantity", errors)

        self.assertEqual(errors["quantity"], "La cantidad debe ser un número entero válido")
    
    def test_ticket_validate_with_amount_of_places_greater_than_4(self):
        """
        Test que verifica la validación de tickets con que hagan que superen la cantidad de 4 lugares como máximo por usuario.
        """

        errors = Ticket.validate(
            quantity=5,
            type="VIP",
            event=self.event,
            user=self.user,    
        )

        self.assertIn("quantity", errors)

        self.assertEqual(errors["quantity"], "Puedes comprar 4 lugares como máximo.")
    
    def test_ticket_validate_with_quantity_as_string(self):
        """
        Test que verifica la validación de tickets con la cantidad como string.
        """

        errors = Ticket.validate(
            quantity="a",
            type="VIP",
            event=self.event,
            user=self.user,    
        )

        self.assertIn("quantity", errors)

        self.assertEqual(errors["quantity"], "La cantidad debe ser un número entero válido")