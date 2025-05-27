from django.test import TestCase
from app.forms import TicketForm
from app.models import Event, User, Ticket, Venue # Importa Venue
from django.db.models import Sum 
from datetime import datetime
from django.utils.timezone import make_aware



class TicketFormUnitTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user1", password="pass")
        
        #Crea una instancia de Venue 
        self.venue = Venue.objects.create(
            name="Test Venue",
            address="123 Test St",
            city="Test City",
            capacity=100, 
            contact="test"
        )

        #Crea una instancia de Evento, asignándole el Venue 
        self.event = Event.objects.create(
            title="Evento Test",
            description="Una descripción de prueba",
            scheduled_at=make_aware(datetime(2025, 12, 31, 19, 0, 0)),
            organizer=self.user, 
            venue=self.venue 
        )

    # Comprueba que el formulario falla correctamente cuando supera el maximo.
    def test_exceed_maximum_tickets(self):
    
        Ticket.objects.create(user=self.user, event=self.event, quantity=3, type='GENERAL') 
        form = TicketForm(data={
            'quantity': 2, 
            'type': 'GENERAL', 
            'card_name': 'Juan Perez', 
            'card_number': '1234567890123', 
            'expiration_date': '12/30', 
            'cvv': '123', 
            'accept_terms': True
        }, user=self.user, event=self.event)
        
        self.assertFalse(form.is_valid()) # si exede el tope 4 entradas is_valid() devuelve false, por ende la asecion es verdera y se continua con la segunda
        self.assertIn("No puede comprar más de 4 entradas para este evento.", str(form.errors)) #la asercion es verdadera si encuentra esa cadena de caracteres dentro de los errores del forms
        

    # comprueba que el formulario pasa correctamente cuando esta por debajo de la cantidad maxima de tickets
    def test_valid_initial_ticket_purchase(self):
             
        form_data = {
            'quantity': 3, 
            'type': 'GENERAL', 
            'card_name': 'Juan Perez', 
            'card_number': '1234567890123', 
            'expiration_date': '12/30', 
            'cvv': '123', 
            'accept_terms': True
        }
        
        form = TicketForm(data=form_data, user=self.user, event=self.event)
        
        self.assertTrue(form.is_valid())

    # comprueba que el formulario pasa correctamente cuando es igual a la cantidad maxima de tickets
    def test_valid_additional_ticket_purchase(self):
       
        Ticket.objects.create(user=self.user, event=self.event, quantity=2, type='GENERAL')
        
        form_data = {
            'quantity': 2, 
            'type': 'GENERAL', 
            'card_name': 'Juan Perez', 
            'card_number': '1234567890123', 
            'expiration_date': '12/30', 
            'cvv': '123', 
            'accept_terms': True
        }

        form = TicketForm(data=form_data, user=self.user, event=self.event)
        
        self.assertTrue(form.is_valid())
        
