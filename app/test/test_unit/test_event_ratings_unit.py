from django.test import TestCase
from app.models import Event, Venue, Rating, User


class EventRatingTests(TestCase):
    def setUp(self):
        # Crear organizador
        self.organizer = self._create_test_user(
            username='organizador',
            email='organizador@test.com',
            password='testpass123',
            is_organizer=True
        )
        
        self.user = self._create_test_user(
            username='usuario',
            email='usuario@test.com',
            password='testpass123',
            is_organizer=False
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

    def _create_test_user(self, username, email, password, is_organizer=False):
        """Helper method para crear usuarios de prueba - optimizado para evitar repetición"""
        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_organizer=is_organizer
        )

    def _create_multiple_ratings(self, ratings_data):
        """Helper method para crear múltiples ratings usando bulk_create - optimizado para performance"""
        ratings_to_create = [
            Rating(
                event=self.event,
                user=self.user,
                **rating_data
            )
            for rating_data in ratings_data
        ]
        return Rating.objects.bulk_create(ratings_to_create)

    def _verify_rating_stats(self, expected_average, expected_count):
        """Helper method para verificar estadísticas de ratings - optimizado para evitar repetición"""
        self.assertEqual(self.event.get_average_rating(), expected_average)
        self.assertEqual(self.event.get_rating_count(), expected_count)

    def test_get_average_rating_with_no_ratings(self):
        """Test que verifica que el promedio es 0 cuando no hay calificaciones"""
        self._verify_rating_stats(expected_average=0, expected_count=0)

    def test_get_average_rating_with_single_rating(self):
        """Test que verifica el cálculo del promedio con una sola calificación"""
        # Crear una calificación usando método helper
        ratings_data = [
            {
                'rating': 4,
                'title': 'Test Rating',
                'text': 'Test Review'
            }
        ]
        self._create_multiple_ratings(ratings_data)
        
        self._verify_rating_stats(expected_average=4.0, expected_count=1)

    def test_get_average_rating_with_multiple_ratings(self):
        """Test que verifica el cálculo del promedio con múltiples calificaciones"""
        ratings_data = [
            {'rating': 5, 'title': 'Tremendo', 'text': 'El mejor evento de mi vida'},
            {'rating': 4, 'title': 'Bastante bueno', 'text': 'Muy bueno, me encantó'},
            {'rating': 3, 'title': 'Zafa', 'text': 'Antes de ir a la casa de mi abuelo, prefiero asistir a este evento'},
            {'rating': 2, 'title': 'Gasté plata al p', 'text': 'Creo que prefiero ir a la casa de mi abuelo'},
            {'rating': 1, 'title': 'Devuelvan la guita', 'text': 'Les voy a romper toda la vidriera que evento malo'}
        ]
        
        self._create_multiple_ratings(ratings_data)
        
        # El promedio debería ser 3.0 (suma de todas las calificaciones / cantidad)
        self._verify_rating_stats(expected_average=3.0, expected_count=5)

    def test_get_average_rating_decimal_precision(self):
        """Test que verifica la precisión decimal del promedio"""
        # Crear calificaciones que resulten en un promedio con decimales usando método helper
        ratings_data = [
            {
                'rating': 5,
                'title': 'Test Rating 1',
                'text': 'Test Review 1'
            },
            {
                'rating': 4,
                'title': 'Test Rating 2',
                'text': 'Test Review 2'
            }
        ]
        self._create_multiple_ratings(ratings_data)
        
        # El promedio debería ser 4.5
        self._verify_rating_stats(expected_average=4.5, expected_count=2)

    def test_get_rating_count_after_deletion(self):
        """Test que verifica el conteo de calificaciones después de eliminar una"""
        # Crear múltiples calificaciones usando método helper
        ratings_data = [
            {
                'rating': 5,
                'title': 'Test Rating 1',
                'text': 'Test Review 1'
            },
            {
                'rating': 4,
                'title': 'Test Rating 2',
                'text': 'Test Review 2'
            }
        ]
        created_ratings = self._create_multiple_ratings(ratings_data)
        
        # Verificar conteo inicial usando método helper
        self._verify_rating_stats(expected_average=4.5, expected_count=2)
        
        # Eliminar una calificación - optimizado para mejor performance
        if created_ratings:
            created_ratings[0].delete()
        
        # Verificar conteo después de eliminar usando método helper
        self._verify_rating_stats(expected_average=4.0, expected_count=1)
