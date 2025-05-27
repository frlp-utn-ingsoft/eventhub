from django.test import TestCase
from django.utils import timezone
import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from app.models import Event, User

class UserModelTest(TestCase):
    def setUp(self):
        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            price_general=Decimal('100.00'),
            price_vip=Decimal('200.00')
        )

    def test_marcar_evento_favorito(self):
        self.organizer.marcar_evento_favorito(self.event)
        self.assertIn(self.event, self.organizer.favorite_events.all())

    def test_desmarcar_evento_favorito(self):
        self.organizer.favorite_events.add(self.event)
        self.organizer.desmarcar_evento_favorito(self.event)
        self.assertNotIn(self.event, self.organizer.favorite_events.all())

    def test_es_evento_favorito_true(self):
        self.organizer.favorite_events.add(self.event)
        self.assertTrue(self.organizer.es_evento_favorito(self.event))

    def test_es_evento_favorito_false(self):
        self.assertFalse(self.organizer.es_evento_favorito(self.event))
