from django.urls import reverse
from django.test import TestCase
from app.models import Event, Rating, User, Venue
from django.utils import timezone

class RatingAverageVisibilityTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username="organizer", password="password123", is_organizer=True)
        self.attendee = User.objects.create_user(username="usuario", password="password123", is_organizer=False)

        self.venue = Venue.objects.create(
            name='Auditorio UTN',
            address='Av. Siempreviva 742',
            capacity=200
        )
        
        self.event1 = Event.objects.create(
            title='Concierto de prueba',
            description='Un evento de integración',
            scheduled_at=timezone.now(),
            organizer=self.organizer,
            venue=self.venue
        )

        Rating.objects.create(evento=self.event1, usuario=self.organizer, titulo="Muy bueno", calificacion=4, texto="Me gustó mucho")
        Rating.objects.create(evento=self.event1, usuario=self.attendee, titulo="No me gusto", calificacion=2)
    
    def test_rating_average_visible_only_to_organizer(self):
        url = reverse("event_detail", args=[self.event1.id])

        #No autenticado
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

        #Autenticado, pero no organizador
        self.client.login(username="usuario", password="password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Promedio de rating")
        self.client.logout()

        #Autenticado, y organizador
        self.client.login(username="organizer", password="password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Calificación promedio")
        self.assertContains(response, "3,0 / 5")

        
        