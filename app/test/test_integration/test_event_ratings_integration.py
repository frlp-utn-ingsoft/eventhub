from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from app.models import Event, Venue, Rating
from decimal import Decimal

User = get_user_model()

class EventRatingIntegrationTests(TestCase):
    def setUp(self):
        # Crear usuarios
        self.organizer = User.objects.create_user(
            username='organizador',
            email='organizador@test.com',
            password='testpass123',
            is_organizer=True
        )
        
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
        
        # Crear cliente HTTP
        self.client = Client()
        
        # Obtener el ID del evento después de crearlo
        self.event_id = Event.objects.get(title='Test Event').pk
        self.event_detail_url = reverse('event_detail', kwargs={'event_id': self.event_id})

    def test_organizer_can_see_average_rating_in_event_detail(self):
        """Test que verifica que el organizador puede ver el promedio de calificaciones en el detalle del evento"""
        # Crear algunas calificaciones
        Rating.objects.create(
            event=self.event,
            user=self.user1,
            rating=5,
            title='Excelente evento',
            text='Muy bueno'
        )
        Rating.objects.create(
            event=self.event,
            user=self.user2,
            rating=3,
            title='Evento regular',
            text='Podría mejorar'
        )
        
        # Iniciar sesión como organizador
        self.client.force_login(self.organizer)
        
        # Obtener la página de detalle del evento
        response = self.client.get(self.event_detail_url)
        
        # Verificar que la respuesta es exitosa
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el promedio se muestra en la página
        self.assertContains(response, 'Calificación promedio:')
        self.assertContains(response, '4.0 / 5.0')
        self.assertContains(response, '(2 calificaciones)')
        
        # Verificar que se muestran todas las calificaciones individuales
        self.assertContains(response, 'Excelente evento')
        self.assertContains(response, 'Evento regular')
        self.assertContains(response, '5')
        self.assertContains(response, '3')

    def test_average_rating_updates_after_new_rating(self):
        """Test que verifica que el promedio se actualiza correctamente después de agregar una nueva calificación"""
        # Iniciar sesión como usuario1
        self.client.force_login(self.user1)
        
        # Crear una calificación inicial
        Rating.objects.create(
            event=self.event,
            user=self.user1,
            rating=4,
            title='Buen evento',
            text='Me gustó'
        )
        
        # Iniciar sesión como organizador
        self.client.force_login(self.organizer)
        
        # Verificar el promedio inicial
        response = self.client.get(self.event_detail_url)
        self.assertContains(response, '4.0 / 5.0')
        self.assertContains(response, '(1 calificaciones)')
        
        # Iniciar sesión como usuario2
        self.client.force_login(self.user2)
        
        # Crear una nueva calificación
        Rating.objects.create(
            event=self.event,
            user=self.user2,
            rating=5,
            title='Excelente',
            text='Superó mis expectativas'
        )
        
        # Volver a iniciar sesión como organizador
        self.client.force_login(self.organizer)
        
        # Verificar que el promedio se actualizó
        response = self.client.get(self.event_detail_url)
        self.assertContains(response, '4.5 / 5.0')
        self.assertContains(response, '(2 calificaciones)')

    def test_average_rating_updates_after_rating_deletion(self):
        """Test que verifica que el promedio se actualiza correctamente después de eliminar una calificación"""
        # Crear dos calificaciones
        rating1 = Rating.objects.create(
            event=self.event,
            user=self.user1,
            rating=5,
            title='Excelente',
            text='Muy bueno'
        )
        Rating.objects.create(
            event=self.event,
            user=self.user2,
            rating=3,
            title='Regular',
            text='Normal'
        )
        
        # Iniciar sesión como organizador
        self.client.force_login(self.organizer)
        
        # Verificar el promedio inicial
        response = self.client.get(self.event_detail_url)
        self.assertContains(response, '4.0 / 5.0')
        self.assertContains(response, '(2 calificaciones)')
        
        # Eliminar una calificación
        rating1.delete()
        
        # Verificar que el promedio se actualizó
        response = self.client.get(self.event_detail_url)
        self.assertContains(response, '3.0 / 5.0')
        self.assertContains(response, '(1 calificaciones)')

    def test_no_ratings_message_displayed(self):
        """Test que verifica que se muestra el mensaje correcto cuando no hay calificaciones"""
        # Iniciar sesión como organizador
        self.client.force_login(self.organizer)
        
        # Verificar que no se muestra el promedio
        response = self.client.get(self.event_detail_url)
        self.assertNotContains(response, 'Calificación promedio:')
        self.assertContains(response, 'No hay reseñas todavía. ¡Sé el primero en dejar una!')
