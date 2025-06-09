from django.test import TestCase
from app.models import Event, Venue, Rating, User


class EventRatingTests(TestCase):
    def setUp(self):
        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username='organizador',
            email='organizador@test.com',
            password='testpass123',
            is_organizer=True
        )
        
        # Crear usuario normal
        self.user = User.objects.create_user(
            username='usuario',
            email='usuario@test.com',
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
        
        # Crear evento
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            scheduled_at='2024-12-31 20:00:00',
            organizer=self.organizer,
            venue=self.venue
        )

    def test_get_average_rating_with_no_ratings(self):
        """Test que verifica que el promedio es 0 cuando no hay calificaciones"""
        self.assertEqual(self.event.get_average_rating(), 0)
        self.assertEqual(self.event.get_rating_count(), 0)

    def test_get_average_rating_with_single_rating(self):
        """Test que verifica el cálculo del promedio con una sola calificación"""
        Rating.objects.create(
            event=self.event,
            user=self.user,
            rating=4,
            title='Test Rating',
            text='Test Review'
        )
        
        self.assertEqual(self.event.get_average_rating(), 4.0)
        self.assertEqual(self.event.get_rating_count(), 1)

    def test_get_average_rating_with_multiple_ratings(self):
        """Test que verifica el cálculo del promedio con múltiples calificaciones"""
        ratings_data = [
            {'rating': 5, 'title': 'Tremendo', 'text': 'El mejor evento de mi vida'},
            {'rating': 4, 'title': 'Bastante bueno', 'text': 'Muy bueno, me encantó'},
            {'rating': 3, 'title': 'Zafa', 'text': 'Antes de ir a la casa de mi abuelo, prefiero asistir a este evento'},
            {'rating': 2, 'title': 'Gasté plata al p', 'text': 'Creo que prefiero ir a la casa de mi abuelo'},
            {'rating': 1, 'title': 'Devuelvan la guita', 'text': 'Les voy a romper toda la vidriera que evento malo'}
        ]
        
        ratings_to_create = [
            Rating(
                event=self.event,
                user=self.user,
                **rating_data
            )
            for rating_data in ratings_data
        ]
        Rating.objects.bulk_create(ratings_to_create)
        
        # El promedio debería ser 3.0 (suma de todas las calificaciones / cantidad)
        self.assertEqual(self.event.get_average_rating(), 3.0)
        self.assertEqual(self.event.get_rating_count(), 5)

    def test_get_average_rating_decimal_precision(self):
        """Test que verifica la precisión decimal del promedio"""
        # Crear calificaciones que resulten en un promedio con decimales
        Rating.objects.create(
            event=self.event,
            user=self.user,
            rating=5,
            title='Test Rating 1',
            text='Test Review 1'
        )
        Rating.objects.create(
            event=self.event,
            user=self.user,
            rating=4,
            title='Test Rating 2',
            text='Test Review 2'
        )
        
        # El promedio debería ser 4.5
        self.assertEqual(self.event.get_average_rating(), 4.5)
        self.assertEqual(self.event.get_rating_count(), 2)

    def test_get_rating_count_after_deletion(self):
        """Test que verifica el conteo de calificaciones después de eliminar una"""
        # Crear dos calificaciones
        rating1 = Rating.objects.create(
            event=self.event,
            user=self.user,
            rating=5,
            title='Test Rating 1',
            text='Test Review 1'
        )
        Rating.objects.create(
            event=self.event,
            user=self.user,
            rating=4,
            title='Test Rating 2',
            text='Test Review 2'
        )
        
        # Verificar conteo inicial
        self.assertEqual(self.event.get_rating_count(), 2)
        
        # Eliminar una calificación
        rating1.delete()
        
        # Verificar conteo después de eliminar
        self.assertEqual(self.event.get_rating_count(), 1)
        self.assertEqual(self.event.get_average_rating(), 4.0)
