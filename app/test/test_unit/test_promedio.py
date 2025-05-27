import datetime
from django.test import TestCase
from app.models import User,Event, Rating
from django.utils import timezone

class PromedioTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador_test",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
        )
    def test_promedio_sin_valoraciones(self):
        ratings = Rating.objects.filter(event=self.event)
        total = sum([r.rating for r in ratings])
        count = ratings.count()
        promedio = total / count if count > 0 else None
        self.assertIsNone(promedio)
        
    def test_promedio_con_valoraciones(self):
        Rating.objects.create(event=self.event, user=self.organizer, title="Buena", text="Me gustó", rating=4)
        Rating.objects.create(event=self.event, user=self.organizer, title="Regular", text="Podría ser mejor", rating=2)
        ratings = Rating.objects.filter(event=self.event)
        total = sum([r.rating for r in ratings])
        count = ratings.count()
        promedio = total / count if count > 0 else None
        self.assertEqual(promedio, 3.0)  # promedio  (4+2)/2 = 3.0