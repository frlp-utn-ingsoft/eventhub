from django.utils.timezone import now, timedelta
from app.models import Event, Ticket, Venue, User, SurveyResponse
from .base import BaseE2ETest
from playwright.sync_api import expect # type: ignore

class SurveyE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()

        self.organizer = User.objects.create_user(
            username="organizer_test",
            email="organizer@example.com",
            password="password123",
            is_organizer=True
        )

        self.user = User.objects.create_user(
            username="usuario_test",
            email="user@example.com",
            password="password123"
        )

        self.venue = Venue.objects.create(
            name="Venue Test",
            address="Calle Test",
            city="Ciudad Test",
            capacity=300,
            contact="contact@test.com"
        )

        self.event = Event.objects.create(
            title="Evento Encuesta",
            description="Evento para test encuesta",
            scheduled_at=now() + timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue
        )

        self.ticket = Ticket.objects.create(
            event=self.event,
            user=self.user,
            quantity=1,
            type="GENERAL"
        )


    def test_user_completes_survey_and_organizer_can_see_it(self):
        # Login usuario y completar encuesta
        self.login_user("usuario_test", "password123")

        self.page.click("text=Comprar Ticket")
        # Llenar el formulario
        self.page.fill("input[name='quantity']", "2")
        self.page.select_option("select[name='type']", "GENERAL")
        self.page.fill("input[name='card_number']", "4242424242424242")
        self.page.fill("input[name='expiration_date']", "12/30")
        self.page.fill("input[name='cvv']", "123")
        self.page.fill("input[name='card_name']", "Juan Test")

        # Aceptar términos
        self.page.check("input[name='accept_terms']")

        # Hacer screenshot antes del submit (opcional)


        # Confirmar compra
        self.page.click("text=Confirmar compra")


        # Click en 5 estrellas (suponiendo input_id 'star-input-satisfaction')
        self.page.click('div.star-rating[data-input-id="star-input-satisfaction"] i.star[data-value="5"]')
        self.page.fill('textarea[name="issue"]', 'Todo perfecto')
        self.page.check('input[name="recommend"]')


        self.page.click("text=Enviar encuesta")

        #self.page.click('button[type="submit"]')
        

        # Login organizador y ver encuestas
        self.login_user("organizer_test", "password123")

        self.login_user("organizer_test", "password123")
        self.page.goto(f"{self.live_server_url}/encuestas/")

        # Verificar que la encuesta está en la lista
        expect(self.page.locator("text=Todo perfecto")).to_be_visible()