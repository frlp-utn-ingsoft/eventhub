from django.urls import reverse
from playwright.sync_api import expect
from django.contrib.auth import get_user_model
from django.utils import timezone
from app.models import Event, Rating, Venue
from app.test.test_e2e.base import BaseE2ETest

User = get_user_model()

class RatingAverageVisibilityTest(BaseE2ETest):
    def setUp(self):
        super().setUp()
        self.mocked_user = User.objects.create_user(
            username="organizer", password="password123", is_organizer=True
        )
        self.mocked_user1 = User.objects.create_user(
            username="usuario", password="password123", is_organizer=False
        )

        self.mocked_venue = Venue.objects.create(
            name='Auditorio UTN',
            address='Av. Siempreviva 742',
            capacity=200
        )
        
        self.mocked_event1 = Event.objects.create(
            title='Concierto de prueba',
            description='Un evento de integración',
            scheduled_at=timezone.now(),
            organizer=self.mocked_user,
            venue=self.mocked_venue
        )

        Rating.objects.create(
            evento=self.mocked_event1,
            usuario=self.mocked_user,
            titulo="Muy bueno",
            calificacion=4,
            texto="Me gustó mucho"
        )
        Rating.objects.create(
            evento=self.mocked_event1,
            usuario=self.mocked_user1,
            titulo="No me gustó",
            calificacion=2
        )
    
    def test_rating_average_visible_only_to_organizer(self):
        self.login_user("organizer","password123")
        self.page.goto(f"{self.live_server_url}/events/{self.mocked_event1.pk}/")
        expect(self.page.get_by_text("Calificación promedio")).to_be_visible()
    
    def test_rating_average_not_visible_to_other_user(self):
        self.login_user("usuario","password123")
        self.page.goto(f"{self.live_server_url}/events/{self.mocked_event1.pk}/")
        expect(self.page.get_by_text("Calificación promedio")).not_to_be_visible()


        
        