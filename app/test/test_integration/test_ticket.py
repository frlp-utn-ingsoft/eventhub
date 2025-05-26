
from django.test import TestCase, Client
from django.urls import reverse
from app.models import Event, Ticket, Venue, User
from datetime import datetime
from django.utils.timezone import make_aware


class TicketCreateIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
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

    #No permite comprar más de 4 tickets totales para un evento, mostrando error.
    def test_user_cannot_buy_more_than_4_tickets(self):
        self.client.login(username='user1', password='pass')
        Ticket.objects.create(user=self.user, event=self.event, quantity=3)

        response = self.client.post(reverse('ticket_create', args=[self.event.id]), { # type: ignore
            'quantity': 2,
            'type': 'GENERAL',
            'card_name': 'Juan Perez',
            'card_number': '1234567890123',
            'expiration_date': '12/30',
            'cvv': '123',
            'accept_terms': True
        })
        
        self.assertContains(response, "No puede comprar más de 4 entradas") #Verifica que la página web devuelta al usuario el mensaje de error
        self.assertEqual(Ticket.objects.filter(user=self.user, event=self.event).count(), 1) # Verifica que no se haya creado ningún nuevo ticket en la base de datos

    #Permite una compra inicial válida (1-4 tickets), redirigiendo a la lista.
    def test_valid_initial_ticket_purchase_integration(self):
            self.client.login(username='user1', password='pass')
            
            initial_ticket_count = Ticket.objects.filter(user=self.user, event=self.event).count() 
            
            form_data = {
                'quantity': 3, 
                'type': 'GENERAL', 
                'card_name': 'Juan Perez', 
                'card_number': '1234567890123', 
                'expiration_date': '12/30', 
                'cvv': '123', 
                'accept_terms': 'on' 
            }
            
            response = self.client.post(reverse('ticket_create', args=[self.event.pk]), form_data)
            
            self.assertRedirects(response, reverse('ticket_list')) 
            
            self.assertEqual(Ticket.objects.filter(user=self.user, event=self.event).count(), initial_ticket_count + 1)
            
    # Permite una compra adicional válida si el total no excede 4, redirigiendo a la lista.
    def test_valid_additional_ticket_purchase_integration(self):
        self.client.login(username='user1', password='pass')
            
        Ticket.objects.create(user=self.user, event=self.event, quantity=2, type='GENERAL')
            
        initial_ticket_count = Ticket.objects.filter(user=self.user, event=self.event).count() 
            
        form_data = {
            'quantity': 2, 
            'type': 'GENERAL', 
            'card_name': 'Juan Perez', 
            'card_number': '1234567890123', 
            'expiration_date': '12/30', 
            'cvv': '123', 
            'accept_terms': 'on' 
        }
            
        response = self.client.post(reverse('ticket_create', args=[self.event.pk]), form_data)
            
        self.assertRedirects(response, reverse('ticket_list')) 

        self.assertEqual(Ticket.objects.filter(user=self.user, event=self.event).count(), initial_ticket_count + 1)
        