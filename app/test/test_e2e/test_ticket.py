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
        
        self.page.goto(f"{self.live_server_url}/events/{self.event1.id}/buy-ticket/")

        # Verificar que existe el input de quantity
        quantity_input = self.page.get_by_label("Cantidad de entradas")
        expect(quantity_input).to_be_visible()

        # Hago focus en el input
        quantity_input.click()

        # Ingreso el valor 5 el cual es invalido, ya que siempre superará el valor inválido el cual es 4
        quantity_input.fill('5')
      
      
        # Completo el campo de la tarjeta mediante el método auxiliar ubicado en base.py
        self.complete_card_data_in_buy_ticket_form()
        
        # Enviar formulario
        self.page.get_by_role("button", name="Confirmar compra").click()

        error_message = self.page.locator("#message-box")
        expect(error_message).to_have_text("No puedes superar el límite de 4 entradas por usario. Puedes comprar 4.")
        