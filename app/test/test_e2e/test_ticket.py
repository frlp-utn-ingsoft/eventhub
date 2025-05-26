
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from app.models import Event, Ticket, Venue 
from datetime import datetime
from django.utils import timezone

User = get_user_model()

class TicketPurchaseE2ETest(TestCase): 
    def setUp(self):
        self.client = Client() 
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.organizer = User.objects.create_user(username='organizeruser', password='organizerpassword')
        self.venue = Venue.objects.create(name='E2E Test Venue', address='123 Test St', city='E2E City', capacity=100)
        self.event = Event.objects.create(
            title='E2E Event Test',
            description='Descripción para el test E2E.',
            scheduled_at=timezone.make_aware(datetime(2025, 12, 31, 20, 0, 0)),
            venue=self.venue,
            organizer=self.organizer
        )
        self.client.login(username='testuser', password='testpassword')

    # Simula y verifica el flujo completo de una compra de ticket exitosa,
    # desde ver el evento hasta la creación del ticket en la BD y
    # su aparición en la lista del usuario
    
    def test_complete_valid_ticket_purchase_flow_from_event_list(self):
        """
        Test E2E: Simula el flujo completo de una compra de ticket exitosa,
        comenzando desde la página de listado de eventos.
        """
        # 1. Acceder a la página de listado de eventos
        event_list_url = reverse('events') 
        response = self.client.get(event_list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.title)
        self.assertContains(response, self.event.description) 
        
        # 2. Simular clic en el botón "Comprar Ticket" que redirige a la página de compra
        purchase_link = reverse('ticket_create', args=[self.event.id]) # type: ignore
        self.assertContains(response, f'href="{purchase_link}"') # Verifica que el enlace exista en la página de listado
        
        # simula un clic del usuario
        response = self.client.get(purchase_link)
        self.assertEqual(response.status_code, 200)

        # Verificar que la página de compra contenga los campos de formulario esperados
        self.assertContains(response, '<input type="text" name="card_name"')
        self.assertContains(response, '<input type="text" name="card_number"')
        self.assertContains(response, '<input type="text" name="expiration_date"')
        self.assertContains(response, '<input type="text" name="cvv"')
        self.assertContains(response, '<input type="text" name="quantity"') 
        self.assertContains(response, '<select name="type"') 

        # 3. Enviar el formulario de compra de tickets con datos válidos
        ticket_data = {
            'quantity': 1,
            'type': 'GENERAL', 
            'card_name': 'Test User',
            'card_number': '1234567890123456',
            'expiration_date': '12/26', 
            'cvv': '123',
            'accept_terms': 'on', 
        }
        
        # Realizar la solicitud POST a la URL de compra, siguiendo cualquier redirección
        response = self.client.post(purchase_link, ticket_data, follow=True) 

        # 4. Verificar que la compra fue exitosa
        self.assertEqual(response.status_code, 200) 
        # Verifica que la aplicación redirige a la página de lista de tickets
        self.assertRedirects(response, reverse('ticket_list')) 
        # Verifica que el título del evento y la cantidad aparecen en la página de tickets del usuario
        self.assertContains(response, self.event.title)
        self.assertContains(response, f"<td>{self.event.title}</td>") 
        
        # Verificar que el ticket se creó correctamente en la base de datos
        self.assertTrue(Ticket.objects.filter(user=self.user, event=self.event, quantity=1).exists())

    # Simula y verifica que la compra falla y
    # se muestra un mensaje de error si se usan datos de tarjeta inválidos,
    # y que no se crea ningún ticket
    def test_ticket_purchase_with_invalid_card_details(self):
        purchase_url = reverse('ticket_create', args=[self.event.id]) # type: ignore
        
        # Datos de compra con un número de tarjeta inválido 
        invalid_ticket_data = {
            'quantity': 1,
            'type': 'GENERAL',
            'card_name': 'Invalid User',
            'card_number': '123',
            'expiration_date': '12/26',
            'cvv': '123',
            'accept_terms': 'on',
        }

        response = self.client.post(purchase_url, invalid_ticket_data, follow=True)

        # La compra debería fallar y el formulario se debería volver a mostrar con errores
        self.assertEqual(response.status_code, 200) 
        
        self.assertContains(response, "Asegúrese de que este valor tenga como mínimo 13 caracteres (tiene 3).") 
        
        self.assertContains(response, "Por favor, corrige los siguientes errores:")
        self.assertContains(response, '<ul class="errorlist" id="id_card_number_error">')

        self.assertContains(response, '<input type="text" name="card_number"') # asegura que el formulario siga ahí

        # Asegurarse de que NO se haya creado ningún ticket
        self.assertFalse(Ticket.objects.filter(user=self.user, event=self.event).exists())