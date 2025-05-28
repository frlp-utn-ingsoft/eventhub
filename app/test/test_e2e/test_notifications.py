from playwright.sync_api import expect
from app.models import Notification, User, Event, Venue, Ticket
from app.test.test_e2e.base import BaseE2ETest

class NotificationBaseTest(BaseE2ETest):
    def setUp(self):
        super().setUp()

        self.mocked_user = User.objects.create_user(username="regular", password="password123", is_organizer=False)
        self.mocked_organizer_user = User.objects.create_user(username="admin", password="password123", is_organizer=True)
        self.mocked_venue = Venue.objects.create(
            name="Centro Cultural Recoleta",
            address="Junín 1930",
            capacity=500,
            country="AR",
            city="Buenos Aires"
        )

        self.event_mocked = Event.objects.create(
            title="Mocked Event",
            description="Test description",
            scheduled_at="2025-12-01T10:00:00Z",
            organizer=self.mocked_organizer_user,
            venue=self.mocked_venue
        )

        self.mocked_notification = Notification.new(
            [self.mocked_user, self.mocked_organizer_user], 
            self.event_mocked,
            "This is a title", 
            "This is a message", 
            "LOW"
        )

        self.mocked_ticket = Ticket.objects.create(
            user=self.mocked_user,
            event=self.event_mocked,
            ticket_code=2,
            quantity=2,  
            type='vip'
        )

class NotificationDisplayTest(NotificationBaseTest):
    def test_notifications_page_display_as_organizer(self):
    
        self.login_user("admin", "password123")
        self.page.goto(f"{self.live_server_url}/notifications/")

        header = self.page.locator("h1")
        expect(header).to_have_text("Notificaciones")
        expect(header).to_be_visible()

        table = self.page.locator("table")
        expect(table).to_be_visible()

        create_btn = self.page.locator("a.btn.btn-primary", has_text="Crear Notificación")
        expect(create_btn).to_be_visible()

    def test_notifications_page_regular_user(self):
        self.login_user("regular", "password123")

        self.page.goto(f"{self.live_server_url}/notifications/")

        header = self.page.locator("h1.fw-bold")
        expect(header).to_contain_text("Notificaciones")

        badge = header.locator("span.badge.bg-danger")
        expect(badge).to_be_visible()
        expect(badge).to_have_text("1 nuevas")

        mark_all_btn = self.page.locator("a.btn.btn-outline-primary", has_text="Marcar todas como leídas")
        expect(mark_all_btn).to_be_visible()

class NotificationByEventChangeTest(NotificationBaseTest):
    def test_create_notification_by_event_change(self):
        self.login_user("admin", "password123")

        self.page.goto(f"{self.live_server_url}/my_events/")

        self.page.get_by_role("link", name="Editar").first.click()

        expect(self.page).to_have_url(f"{self.live_server_url}/events/{self.event_mocked.id}/edit/")

        header = self.page.locator("h1")
        expect(header).to_have_text("Editar evento")
        expect(header).to_be_visible()

        title = self.page.get_by_label("Título del Evento")
        title.fill("Titulo editado")

        description = self.page.get_by_label("Descripción")
        description.fill("Descripcion Editada")

        date = self.page.get_by_label("Fecha")
        date.fill("2025-04-20")

        time = self.page.get_by_label("Hora")
        time.fill("04:00")

        self.page.get_by_role("button", name="Guardar Cambios").click()

        self.page.goto(f"{self.live_server_url}/notifications/")
        
        notification_title = self.page.locator("tbody tr td").filter(has_text="Evento Modificado")
        expect(notification_title).to_be_visible()

        notification_priority = self.page.locator("tbody tr td").filter(has_text="Baja").nth(1)
        expect(notification_priority).to_be_visible()