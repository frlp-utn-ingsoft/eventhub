from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import TestCase
from app.models import Event, Rating, Venue

User = get_user_model()

class RatingAverageCalculation(TestCase):

    def setUp(self):
        self.organizer = User.objects.create_user(username="organizer", password="pass")
        self.venue_mocked = Venue.objects.create(
            name="Auditorio Nacional",
            address="60 y 124",
            capacity=5000,
            country="ARG",  
            city="La Plata"
        )
        self.event = Event.objects.create(
            title="Evento Test", 
            organizer=self.organizer, 
            scheduled_at=timezone.now(), 
            venue=self.venue_mocked
        )

    def test_rating_average_calculation(self):
        Rating.objects.create(
            evento=self.event, usuario=self.organizer,
            titulo="Muy Bueno", calificacion=5, texto="El evento estuvo muy interesante"
        )

        Rating.objects.create(
            evento=self.event, usuario=User.objects.create_user(username="user2", password="pass"),
            titulo="No me intereso", calificacion=3, texto="El evento estuvo bien, pero puede mejorar"
        )

        Rating.objects.create(
            evento=self.event, usuario=User.objects.create_user(username="user3", password="pass"),
            titulo="Malo", calificacion=1, texto="No me gusto nada"
        )

        average = self.event.rating_average
        self.assertEqual(round(average, 1), 3.0)
