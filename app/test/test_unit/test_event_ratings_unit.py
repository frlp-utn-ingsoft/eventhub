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
        
        # Crear múltiples usuarios para diferentes ratings
        self.users = self._create_multiple_users(count=5, base_username='usuario')
        
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
        
        # Crear ratings base para diferentes escenarios
        # Rating 1: 4 estrellas
        self.rating1 = Rating.objects.create(
            event=self.event,
            user=self.users[0],
            rating=4,
            title='Test Rating 1',
            text='Test Review 1'
        )
        
        # Rating 2: 5 estrellas
        self.rating2 = Rating.objects.create(
            event=self.event,
            user=self.users[1],
            rating=5,
            title='Test Rating 2',
            text='Test Review 2'
        )
        
        # Rating 3: 3 estrellas
        self.rating3 = Rating.objects.create(
            event=self.event,
            user=self.users[2],
            rating=3,
            title='Test Rating 3',
            text='Test Review 3'
        )
        
        # Rating 4: 2 estrellas
        self.rating4 = Rating.objects.create(
            event=self.event,
            user=self.users[3],
            rating=2,
            title='Test Rating 4',
            text='Test Review 4'
        )
        
        # Rating 5: 1 estrella
        self.rating5 = Rating.objects.create(
            event=self.event,
            user=self.users[4],
            rating=1,
            title='Test Rating 5',
            text='Test Review 5'
        )

    def _create_test_user(self, username, email, password, is_organizer=False):
        """Helper method para crear usuarios de prueba - optimizado para evitar repetición"""
        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_organizer=is_organizer
        )

    def _create_multiple_users(self, count: int, base_username: str = 'usuario') -> list:
        """Helper method para crear múltiples usuarios usando bulk_create - optimizado para performance"""
        users_to_create = [
            User(
                username=f'{base_username}{i}',
                email=f'{base_username}{i}@test.com',
                password='testpass123'
            )
            for i in range(count)
        ]
        return User.objects.bulk_create(users_to_create)

    def _verify_rating_stats(self, expected_average, expected_count):
        """Helper method para verificar estadísticas de ratings - optimizado para evitar repetición"""
        self.assertEqual(self.event.get_average_rating(), expected_average)
        self.assertEqual(self.event.get_rating_count(), expected_count)

    def test_get_average_rating_with_no_ratings(self):
        """Test que verifica que el promedio es 0 cuando no hay calificaciones"""
        # Crear un nuevo evento sin ratings
        empty_event = Event.objects.create(
            title='Empty Event',
            description='Empty Description',
            scheduled_at='2024-12-31 21:00:00',
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Verificar estadísticas del evento vacío
        self.assertEqual(empty_event.get_average_rating(), 0)
        self.assertEqual(empty_event.get_rating_count(), 0)

    def test_get_average_rating_with_single_rating(self):
        """Test que verifica el cálculo del promedio con una sola calificación"""
        # Crear un nuevo evento
        single_event = Event.objects.create(
            title='Single Rating Event',
            description='Single Description',
            scheduled_at='2024-12-31 22:00:00',
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Crear una calificación directamente en el evento single_event
        Rating.objects.create(
            event=single_event,
            user=self.users[0],
            rating=4,
            title='Test Rating',
            text='Test Review'
        )
        
        # Verificar estadísticas del evento con un rating
        self.assertEqual(single_event.get_average_rating(), 4.0)
        self.assertEqual(single_event.get_rating_count(), 1)

    def test_get_average_rating_with_multiple_ratings(self):
        """Test que verifica el cálculo del promedio con múltiples calificaciones"""
        # Los ratings ya están creados
        self._verify_rating_stats(expected_average=3.0, expected_count=5)

    def test_get_average_rating_decimal_precision(self):
        """Test que verifica la precisión decimal del promedio"""
        # Crear un nuevo evento
        decimal_event = Event.objects.create(
            title='Decimal Event',
            description='Decimal Description',
            scheduled_at='2024-12-31 23:00:00',
            organizer=self.organizer,
            venue=self.venue
        )
        
        # Crear calificaciones
        Rating.objects.create(
            event=decimal_event,
            user=self.users[0],
            rating=5,
            title='Test Rating 1',
            text='Test Review 1'
        )
        
        Rating.objects.create(
            event=decimal_event,
            user=self.users[1],
            rating=4,
            title='Test Rating 2',
            text='Test Review 2'
        )
        
        self.assertEqual(decimal_event.get_average_rating(), 4.5)
        self.assertEqual(decimal_event.get_rating_count(), 2)

    def test_get_rating_count_after_deletion(self):
        """Test que verifica el conteo de calificaciones después de eliminar una"""
        # Usar los ratings creados
        self._verify_rating_stats(expected_average=3.0, expected_count=5)
        
        # Eliminar una calificación
        self.rating1.delete()
        
        # Verificar conteo después de eliminar (ahora 5+3+2+1 = 11, promedio = 2.75)
        self.assertEqual(self.event.get_average_rating(), 2.75)
        self.assertEqual(self.event.get_rating_count(), 4)
