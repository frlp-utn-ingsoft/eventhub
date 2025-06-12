from django.test import TestCase
from app.models import Event, Venue, Rating, User
from django.utils import timezone
import datetime


class EventRatingTests(TestCase):
    def setUp(self):
        # Crear organizador
        self.organizer = User.objects.create_user(
            username='organizador',
            email='organizador@test.com',
            password='testpass123',
            is_organizer=True
        )
        
        # Crear usuarios directamente sin usar bucles
        self.user1 = User.objects.create_user(
            username='usuario1',
            email='usuario1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='usuario2',
            email='usuario2@test.com',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            username='usuario3',
            email='usuario3@test.com',
            password='testpass123'
        )
        self.user4 = User.objects.create_user(
            username='usuario4',
            email='usuario4@test.com',
            password='testpass123'
        )
        self.user5 = User.objects.create_user(
            username='usuario5',
            email='usuario5@test.com',
            password='testpass123'
        )
        
        # Crear venue
        self.venue = Venue.objects.create(
            name='Test Venue',
            adress='Test Address',
            city='Test City',
            capacity=100,
            contact='test@venue.com'
        )
        
        # Crear eventos para diferentes tests
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            scheduled_at=timezone.make_aware(datetime.datetime(2024, 12, 31, 20, 0, 0)),
            organizer=self.organizer,
            venue=self.venue
        )

        self.empty_event = Event.objects.create(
            title='Empty Event',
            description='Empty Description',
            scheduled_at=timezone.make_aware(datetime.datetime(2024, 12, 31, 21, 0, 0)),
            organizer=self.organizer,
            venue=self.venue
        )

        self.single_event = Event.objects.create(
            title='Single Rating Event',
            description='Single Description',
            scheduled_at=timezone.make_aware(datetime.datetime(2024, 12, 31, 22, 0, 0)),
            organizer=self.organizer,
            venue=self.venue
        )

        self.decimal_event = Event.objects.create(
            title='Decimal Event',
            description='Decimal Description',
            scheduled_at=timezone.make_aware(datetime.datetime(2024, 12, 31, 23, 0, 0)),
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Crear ratings base para diferentes escenarios
        # Rating 1: 4 estrellas
        self.rating1 = Rating.objects.create(
            event=self.event,
            user=self.user1,
            rating=4,
            title='Test Rating 1',
            text='Test Review 1'
        )
        
        # Rating 2: 5 estrellas
        self.rating2 = Rating.objects.create(
            event=self.event,
            user=self.user2,
            rating=5,
            title='Test Rating 2',
            text='Test Review 2'
        )
        
        # Rating 3: 3 estrellas
        self.rating3 = Rating.objects.create(
            event=self.event,
            user=self.user3,
            rating=3,
            title='Test Rating 3',
            text='Test Review 3'
        )
        
        # Rating 4: 2 estrellas
        self.rating4 = Rating.objects.create(
            event=self.event,
            user=self.user4,
            rating=2,
            title='Test Rating 4',
            text='Test Review 4'
        )
        
        # Rating 5: 1 estrella
        self.rating5 = Rating.objects.create(
            event=self.event,
            user=self.user5,
            rating=1,
            title='Test Rating 5',
            text='Test Review 5'
        )

        # Crear rating para single_event
        self.single_rating = Rating.objects.create(
            event=self.single_event,
            user=self.user1,
            rating=4,
            title='Test Rating',
            text='Test Review'
        )

        # Crear ratings para decimal_event
        self.decimal_rating1 = Rating.objects.create(
            event=self.decimal_event,
            user=self.user1,
            rating=5,
            title='Test Rating 1',
            text='Test Review 1'
        )
        
        self.decimal_rating2 = Rating.objects.create(
            event=self.decimal_event,
            user=self.user2,
            rating=4,
            title='Test Rating 2',
            text='Test Review 2'
        )

    def _verify_rating_stats(self, expected_average, expected_count):
        """Helper method para verificar estadísticas de ratings - optimizado para evitar repetición"""
        self.assertEqual(self.event.get_average_rating(), expected_average)
        self.assertEqual(self.event.get_rating_count(), expected_count)

    def test_get_average_rating_with_no_ratings(self):
        """Test que verifica que el promedio es 0 cuando no hay calificaciones"""
        # Verificar estadísticas del evento vacío
        self.assertEqual(self.empty_event.get_average_rating(), 0)
        self.assertEqual(self.empty_event.get_rating_count(), 0)

    def test_get_average_rating_with_single_rating(self):
        """Test que verifica el cálculo del promedio con una sola calificación"""
        # Verificar estadísticas del evento con un rating
        self.assertEqual(self.single_event.get_average_rating(), 4.0)
        self.assertEqual(self.single_event.get_rating_count(), 1)

    def test_get_average_rating_with_multiple_ratings(self):
        """Test que verifica el cálculo del promedio con múltiples calificaciones"""
        # Los ratings ya están creados en setUp
        self._verify_rating_stats(expected_average=3.0, expected_count=5)

    def test_get_average_rating_decimal_precision(self):
        """Test que verifica la precisión decimal del promedio"""
        self.assertEqual(self.decimal_event.get_average_rating(), 4.5)
        self.assertEqual(self.decimal_event.get_rating_count(), 2)

    def test_get_rating_count_after_deletion(self):
        """Test que verifica el conteo de calificaciones después de eliminar una"""
        # Usar los ratings creados en setUp
        self._verify_rating_stats(expected_average=3.0, expected_count=5)
        
        # Eliminar una calificación
        self.rating1.delete()
        
        # Verificar conteo después de eliminar (ahora 5+3+2+1 = 11, promedio = 2.75)
        self.assertEqual(self.event.get_average_rating(), 2.75)
        self.assertEqual(self.event.get_rating_count(), 4)
