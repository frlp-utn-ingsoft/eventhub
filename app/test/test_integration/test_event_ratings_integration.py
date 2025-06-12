from django.test import TestCase
from django.urls import reverse
from app.models import Event, Venue, Rating, User
from django.utils import timezone
from django.contrib.messages import get_messages
import datetime

class EventRatingsIntegrationTest(TestCase):
    def setUp(self):
        # Crear usuario organizador
        self.organizer = User.objects.create_user(
            username='organizador',
            email='organizador@test.com',
            password='testpass123',
            is_organizer=True
        )
        
        # Crear usuarios normales
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
        
        # Crear venue
        self.venue = Venue.objects.create(
            name='Test Venue',
            adress='Test Address',
            city='Test City',
            capacity=100,
            contact='test@venue.com'
        )
        
        # Crear evento
        event_date = timezone.make_aware(datetime.datetime(2025, 2, 10, 10, 10))
        self.event = Event.objects.create(
            title='Test Event',
            description='Test Description',
            scheduled_at=event_date,
            organizer=self.organizer,
            venue=self.venue
        )

        # Crear ratings iniciales
        self.rating1 = Rating.objects.create(
            event=self.event,
            user=self.user1,
            title='Buen evento',
            text='Regular',
            rating=3
        )

        self.rating2 = Rating.objects.create(
            event=self.event,
            user=self.user2,
            title='Excelente',
            text='Comparado a cuando nació mi hijo, impecable.',
            rating=5
        )

    def test_create_rating_flow(self):
        """Test que verifica el flujo completo de creación de un rating"""
        # 1. Verificar estado inicial
        self.assertEqual(self.event.get_average_rating(), 4.0)  # Promedio de los ratings iniciales
        self.assertEqual(self.event.get_rating_count(), 2)     # Dos ratings iniciales
        
        # 2. Crear rating
        rating_data = {
            'title': 'Excelente evento',
            'text': 'Muy buena organización',
            'rating': 5
        }
        
        # Simular login con usuario3 que no tiene rating
        self.client.login(username='usuario3', password='testpass123')
        
        # Crear rating a través de la vista
        response = self.client.post(
            reverse('create_rating', args=[self.event.id]),
            rating_data
        )
        
        # 3. Verificar redirección
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('event_detail', args=[self.event.id]))
        
        # 4. Verificar que el rating se creó correctamente
        rating = Rating.objects.get(event=self.event, user=self.user3)
        self.assertEqual(rating.title, rating_data['title'])
        self.assertEqual(rating.text, rating_data['text'])
        self.assertEqual(rating.rating, rating_data['rating'])
        
        # 5. Verificar que el promedio se actualizó
        self.event.refresh_from_db()
        self.assertAlmostEqual(self.event.get_average_rating(), 4.33, places=2)  # (3 + 5 + 5) / 3
        self.assertEqual(self.event.get_rating_count(), 3)

    def test_edit_rating_flow(self):
        """Test que verifica el flujo completo de edición de un rating"""
        # 1. Verificar estado inicial
        self.event.refresh_from_db()
        self.assertEqual(self.event.get_average_rating(), 4.0)  # Promedio de los ratings iniciales
        
        # 2. Editar rating
        new_rating_data = {
            'title': 'Excelente evento',
            'text': 'Muy buena organización',
            'rating': 5
        }
        
        # Simular login
        self.client.login(username='usuario1', password='testpass123')
        
        # Editar rating a través de la vista
        response = self.client.post(
            reverse('edit_rating', args=[self.rating1.id]),
            new_rating_data
        )
        
        # 3. Verificar redirección
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('event_detail', args=[self.event.id]))
        
        # 4. Verificar que el rating se actualizó
        self.rating1.refresh_from_db()
        self.assertEqual(self.rating1.title, new_rating_data['title'])
        self.assertEqual(self.rating1.text, new_rating_data['text'])
        self.assertEqual(self.rating1.rating, new_rating_data['rating'])
        
        # 5. Verificar que el promedio se actualizó
        self.event.refresh_from_db()
        self.assertEqual(self.event.get_average_rating(), 5.0)  # (5 + 5) / 2

    def test_delete_rating_flow(self):
        """Test que verifica el flujo completo de eliminación de un rating"""
        # 1. Verificar estado inicial
        self.event.refresh_from_db()
        self.assertEqual(self.event.get_average_rating(), 4.0)  # Promedio de los ratings iniciales
        self.assertEqual(self.event.get_rating_count(), 2)     # Dos ratings iniciales
        
        # 2. Eliminar rating
        # Simular login
        self.client.login(username='usuario1', password='testpass123')
        
        # Eliminar rating a través de la vista
        response = self.client.get(reverse('delete_rating', args=[self.rating1.id]))
        
        # 3. Verificar redirección
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('event_detail', args=[self.event.id]))
        
        # 4. Verificar que el rating se eliminó
        self.assertFalse(Rating.objects.filter(id=self.rating1.id).exists())
        
        # 5. Verificar que el promedio se actualizó
        self.event.refresh_from_db()
        self.assertEqual(self.event.get_average_rating(), 5.0)  # Solo queda el rating de 5
        self.assertEqual(self.event.get_rating_count(), 1)

    def test_rating_permissions(self):
        """Test que verifica los permisos y reglas de negocio de los ratings"""
        # 1. Verificar que el organizador no puede calificar su propio evento
        self.client.login(username='organizador', password='testpass123')
        response = self.client.get(reverse('create_rating', args=[self.event.id]))
        self.assertEqual(response.status_code, 302)  # Redirección
        
        # Obtener mensajes de la respuesta
        messages = list(get_messages(response.wsgi_request))
        message_texts = [str(msg) for msg in messages]
        self.assertTrue('organizadores no pueden calificar sus propios eventos' in ' '.join(message_texts))
        
        # 2. Verificar que un usuario no puede calificar dos veces el mismo evento
        # Intentar segunda calificación
        self.client.login(username='usuario1', password='testpass123')
        response = self.client.get(reverse('create_rating', args=[self.event.id]))
        self.assertEqual(response.status_code, 302)  # Redirección
        
        # Obtener mensajes de la respuesta
        messages = list(get_messages(response.wsgi_request))
        message_texts = [str(msg) for msg in messages]
        self.assertTrue('Ya has calificado este evento' in ' '.join(message_texts))
        
        # 3. Verificar que un usuario no puede editar la calificación de otro
        # Intentar editar como usuario1
        self.client.login(username='usuario1', password='testpass123')
        response = self.client.post(
            reverse('edit_rating', args=[self.rating2.id]),
            {'title': 'Intento de edición', 'rating': 5}
        )
        self.assertEqual(response.status_code, 302)  # Redirección
        
        # Obtener mensajes de la respuesta
        messages = list(get_messages(response.wsgi_request))
        message_texts = [str(msg) for msg in messages]
        self.assertTrue('No tienes permiso para editar esta reseña' in ' '.join(message_texts))
        
        # 4. Verificar que un usuario no puede eliminar la calificación de otro
        response = self.client.get(reverse('delete_rating', args=[self.rating2.id]))
        self.assertEqual(response.status_code, 302)  # Redirección
        self.assertTrue(Rating.objects.filter(id=self.rating2.id).exists())  # El rating sigue existiendo
