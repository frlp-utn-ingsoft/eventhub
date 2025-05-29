import datetime
import re

from django.utils import timezone
from playwright.sync_api import expect

from app.models import Event, User, Ticket, Venue

from app.test.test_e2e.base import BaseE2ETest


class TicketBaseTest(BaseE2ETest):
    """
    Clase base con la configuración común para todos los test de tickets.
    """

    def setUp(self):
        super().setUp()

        # Crear un usuario organizador
    #    self.organizer = User.objects.create_user(
     #       username="organizador",
      #      email="organizador@test.com",
       #     password="password123",
        #    is_organizer=True,
        #)

        # Crear un usuario regular
        #self.regular_user = User.objects.create_user(
         #   username="regular",
          #  email="regular@test.com",
           # password="password123",
            #is_organizer=False,
        #)

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

        ticket_event_2 = Ticket.objects.create(
            quantity=1,
            type="GENERAL",
            event=self.event2,
            user=self.regular_user
        )


class Ticket4PlacesLimitTest(TicketBaseTest):
    """
    Tests relacionados con el límite de cuatro lugares en un evento por ususario.
    """

    def test_limit_in_quantity_input(self):
        """
        Test que verifica que el input de quantity, tenga como límite máximo la cantidad permitida en base a la cantidad de lugares que ya tenga el usuario.
        """
        # Primero verificar como usuario regular
        self.login_user("usuario", "password123")
        self.page.goto(f"{self.live_server_url}/events/2/buy-ticket/")

        # Verificar que existe el input de quantity
        quantity_input = self.page.get_by_label("Cantidad de entradas")
        expect(quantity_input).to_be_visible()

        # Hago focus en el input
        quantity_input.click()

        # Presionar la flecha arriba 4 veces para aumentar el valor de 1 hasta el límite o más
        self.page.keyboard.press("ArrowUp")
        self.page.keyboard.press("ArrowUp")
        self.page.keyboard.press("ArrowUp")
        self.page.keyboard.press("ArrowUp")

        # Verificar que el nuevo valor es "3"
        expect(quantity_input).to_have_value("3")

        # El valor debería ser 3 dado que al ya haber creado un ticket con un lugar para el evento 2, el límite de 4 se reduce a 3.