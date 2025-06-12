import datetime

from django.contrib import messages
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import Event, User, Ticket, Venue

class BaseTicketTestCase(TestCase):
    """
    Clase base con la configuración común para todos los test de tickets.
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

        # Crear una localización de prueba
        self.venue = Venue.objects.create(
            name = "venue__name-test",
            adress = "venue__adress-test",
            city = "venue__city-test",
            capacity = 15000,
            contact = "venue__contac-test"
        )
    
        # Crear algunos eventos de prueba
        self.event1 = Event.objects.create(
            title="Evento 1",
            description="Descripción del evento 1",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue= self.venue
        )

        self.event2 = Event.objects.create(
            title="Evento 2",
            description="Descripción del evento 2",
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            organizer=self.organizer,
            venue= self.venue
        )
        

        # Crear algunos tickets de prueba
        ticket_event_1 = Ticket.objects.create(
            quantity=4,
            type="VIP",
            event=self.event1,
            user=self.regular_user
        )

        # Cliente para hacer peticiones
        self.client = Client()


class BuyTicketViewTest(BaseTicketTestCase):
    """
    Tests para la vista de compra de tickets
    """
    def test_buy_tickets_with_limit_reached(self):
        """
        Verifica que no se permita comprar más tickets cuando se alcanza el límite por usuario/evento.
        """
        # Login con usuario regular
        self.client.login(username="regular", password="password123")

        # Verificar que ya tiene 4 tickets para event1 (creados en setUp)
        self.assertEqual(Ticket.objects.filter(event=self.event1, user=self.regular_user).count(), 1)
        self.assertEqual(Ticket.objects.get(event=self.event1, user=self.regular_user).quantity, 4)

        # 1. Test GET request
        response_get = self.client.get(reverse('buy_ticket', kwargs={'id': self.event1.id}))
        
        # Verificaciones GET
        self.assertEqual(response_get.status_code, 200)
        self.assertTemplateUsed(response_get, "app/buy_ticket.html")
        self.assertEqual(response_get.context['available_tickets_to_buy'], 0)
   

        # 2. Test POST request - intentar comprar más
        response_post = self.client.post(
            reverse('buy_ticket', kwargs={'id': self.event1.id}),
            {'quantity': 1, 'type': 'VIP'},
            follow=True  # Para seguir redirecciones
        )
        
        # Verificaciones POST
        messages_list = list(messages.get_messages(response_post.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), "Lo sentimos. Ya has comprado el máximo disponible de entradas por usuario.")

