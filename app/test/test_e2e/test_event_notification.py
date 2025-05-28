from django.utils.timezone import now, timedelta
from app.models import Event, Ticket, Venue, User
from .base import BaseE2ETest
from playwright.sync_api import expect #type: ignore

class EventNotificationE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()
        self.user = self.create_test_user()

        self.organizer = User.objects.create_user(
            username="organizer_test",
            email="organizer_test@example.com",
            password="password123",
            is_organizer=True
        )

        self.venue1 = Venue.objects.create(
            name="Venue Original",
            address="Calle A",
            city="Ciudad",
            capacity=500,
            contact="mail@test.com"
        )
        self.venue2 = Venue.objects.create(
            name="Venue Nuevo",
            address="Calle B",
            city="Ciudad",
            capacity=700,
            contact="mail2@test.com"
        )

        self.event = Event.objects.create(
            title="Evento E2E",
            description="Descripción",
            scheduled_at=now() + timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue1
        )

        Ticket.objects.create(
            event=self.event,
            user=self.user,
            quantity=2,
            type="GENERAL"
        )

        self.user2 = User.objects.create_user(
            username="segundo_usuario",
            email="segundo@example.com",
            password="password456"
        )

        Ticket.objects.create(
            event=self.event,
            user=self.user2,
            quantity=1,
            type="GENERAL"
        )

    def test_notification_shown_after_event_update(self):
        self.event.scheduled_at += timedelta(hours=2)
        self.event.venue = self.venue2 #type:ignore
        self.event.save()

        self.login_user("usuario_test", "password123")

        self.page.goto(f"{self.live_server_url}/notifications/")

        expect(self.page.locator(f"text=Actualización del evento Evento E2E")).to_be_visible()
        expect(self.page.locator(f"text=ha cambiado")).to_be_visible()
        expect(self.page.locator("h5", has_text=f"{self.venue1.name}")).to_be_visible()
        expect(self.page.locator(f"text={self.venue2.name}")).to_be_visible()

    def test_organizer_creates_notification_for_specific_user_and_user_receives_it(self):

        self.page.goto(f"{self.live_server_url}/accounts/login/")
        self.page.fill('input[name="username"]', self.organizer.username)
        self.page.fill('input[name="password"]', "password123")
        self.page.click('button[type="submit"]')

        self.page.goto(f"{self.live_server_url}/notifications/")
        self.page.click("text=Crear nueva notificación")
        self.page.fill('input[name="title"]', "Notificación a asistentes del evento")
        self.page.fill('textarea[name="message"]', "Mensaje para usuarios")
        self.page.select_option('select[name="event"]', label=f"{self.event.title}")
        self.page.check('input[name="tipo_usuario"][value="all"]')
        self.page.select_option('select[name="priority"]', "Medium")
        self.page.get_by_role("button", name="Enviar Notificación").click()
        expect(self.page.locator("text=Notificación a asistentes del evento")).to_be_visible()
        
        self.page.get_by_role("button", name="Salir").click()
        
        self.page.goto(f"{self.live_server_url}/accounts/login/")
        self.page.fill('input[name="username"]', "segundo_usuario")
        self.page.fill('input[name="password"]', "password456")
        self.page.click('button[type="submit"]')    

        self.page.goto(f"{self.live_server_url}/notifications/")
        expect(self.page.locator("text=Notificación a asistentes del evento")).to_be_visible()
        expect(self.page.locator("text=Mensaje para usuarios")).to_be_visible()

        self.page.click("text=Marcar como leída")
        expect(self.page.locator("text=Ya leída")).to_be_visible()