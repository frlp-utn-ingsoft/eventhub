from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from app.models import Event, Venue, Category,Ticket, Notification
from django.contrib.auth import get_user_model
User = get_user_model()
import datetime

class EventStateIntegrationTest(TestCase):
    def setUp(self):
        # Crear un usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )

        # Crear un usuario regular
        self.regular_user1 = User.objects.create_user(
            username="regular",
            email="regular@test.com",
            password="password123",
            is_organizer=False,
        )
        self.regular_user2 = User.objects.create_user(
            username="regular2",
            email="regular1@test.com",
            password="password123",
            is_organizer=False,
        )
        
        ## Creamos venues
        self.venue1 = Venue.objects.create(name="Lugar 1", capacity=100)
        self.venue2 = Venue.objects.create(name="Lugar 2", capacity=100)

        # Crear algunos eventos de prueba
        self.event1 = Event.objects.create(
            title="Evento 1",
            description="Descripción del evento 1",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue = self.venue1,
        )
        self.client = Client()
        self.user = User.objects.create_user(username='organizer', password='testpass', is_organizer=True)
        self.venue = Venue.objects.create(name="Test Venue", adress="Test Adress", capacity=100)
        self.category = Category.objects.create(name="Music", is_active=True)

        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            organizer=self.organizer,
            venue=self.venue
        )
     # Usuarios con Tickets para el evento 1
        Ticket.objects.create(user=self.regular_user1, event=self.event1, quantity=1, type="GENERAL")
        Ticket.objects.create(user=self.regular_user2, event=self.event1, quantity=1, type="GENERAL")

     


class EventsListViewTest(BaseEventTestCase):
    """Tests para la vista de listado de eventos"""

    def test_events_view_with_login(self):
        """Test que verifica que la vista events funciona cuando el usuario está logueado"""
        # Login con usuario regular
        self.client.login(username="regular", password="password123")

        # Hacer petición a la vista events
        response = self.client.get(reverse("events"))

        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/events.html")
        self.assertIn("events", response.context)
        self.assertIn("user_is_organizer", response.context)
        self.assertEqual(len(response.context["events"]), 2)
        self.assertFalse(response.context["user_is_organizer"])

        # Verificar que los eventos están ordenados por fecha
        events = list(response.context["events"])
        self.assertEqual(events[0].id, self.event1.id)
        self.assertEqual(events[1].id, self.event2.id)

    def test_events_view_with_organizer_login(self):
        """Test que verifica que la vista events funciona cuando el usuario es organizador"""
        # Login con usuario organizador
        self.client.login(username="organizador", password="password123")

        # Hacer petición a la vista events
        response = self.client.get(reverse("events"))

        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["user_is_organizer"])

    def test_events_view_without_login(self):
        """Test que verifica que la vista events redirige a login cuando el usuario no está logueado"""
        # Hacer petición a la vista events sin login
        response = self.client.get(reverse("events"))

        # Verificar que redirecciona al login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))


class EventDetailViewTest(BaseEventTestCase):
    """Tests para la vista de detalle de un evento"""

    def test_event_detail_view_with_login(self):
        """Test que verifica que la vista event_detail funciona cuando el usuario está logueado"""
        # Login con usuario regular
        self.client.login(username="regular", password="password123")

        # Hacer petición a la vista event_detail
        response = self.client.get(reverse("event_detail", args=[self.event1.id]))

        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/event_detail.html")
        self.assertIn("event", response.context)
        self.assertEqual(response.context["event"].id, self.event1.id)
            organizer=self.user,
            venue=self.venue
        )
        self.event.categories.add(self.category)  # Relación M2M

        self.event_id = self.event.id  # Se accede después de crear
        self.venue_id = self.venue.id

        self.client.login(username='organizer', password='testpass')

    def test_event_detail_view_without_login(self):
        """Test que verifica que la vista event_detail redirige a login cuando el usuario no está logueado"""
        # Hacer petición a la vista event_detail sin login
        response = self.client.get(reverse("event_detail", args=[self.event1.id]))

        # Verificar que redirecciona al login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_event_detail_view_with_invalid_id(self):
        """Test que verifica que la vista event_detail devuelve 404 cuando el evento no existe"""
        # Login con usuario regular
        self.client.login(username="regular", password="password123")

        # Hacer petición a la vista event_detail con ID inválido
        response = self.client.get(reverse("event_detail", args=[999]))

        # Verificar respuesta
        self.assertEqual(response.status_code, 404)

    def test_event_get_demand(self):
        """Test de integración que  verifica que la vista event_detail muestra la demanda del evento correctamente y si es alta o baja"""
        # Login como organizador
        self.client.login(username="organizador", password="password123")

        # Demanda baja (sin tickets)
        response = self.client.get(reverse("event_detail", args=[self.event1.id]))
        self.assertContains(response, "Baja demanda")

        # Crear 91 tickets para superar el 90% de ocupación (capacidad 100)
        for i in range(91):
            user = User.objects.create_user(
                username=f"user_{i}",
                email=f"user_{i}@test.com",
                password="password123"
            )
            Ticket.objects.create(
                user=user,
                event=self.event1,
                type="general",
                quantity=1
            )

        
        response = self.client.get(reverse("event_detail", args=[self.event1.id]))
        ##Verificar que la cantidad de entradas vendidas es correcta == 91
        self.assertContains(response, "Entradas vendidas:")
        self.assertContains(response, "91")
        # Demanda alta 
        self.assertContains(response, "Alta demanda")
    


class EventFormViewTest(BaseEventTestCase):
    """Tests para la vista del formulario de eventos"""

    def test_event_form_view_with_organizer(self):
        """Test que verifica que la vista event_form funciona cuando el usuario es organizador"""
        # Login con usuario organizador
        self.client.login(username="organizador", password="password123")

        # Hacer petición a la vista event_form para crear nuevo evento (id=None)
        response = self.client.get(reverse("event_form"))

        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/event_form.html")
        self.assertIn("event", response.context)
        self.assertTrue(response.context["user_is_organizer"])

    def test_event_form_view_with_regular_user(self):
        """Test que verifica que la vista event_form redirige cuando el usuario no es organizador"""
        # Login con usuario regular
        self.client.login(username="regular", password="password123")

        # Hacer petición a la vista event_form
        response = self.client.get(reverse("event_form"))

        # Verificar que redirecciona a events
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("events"))

    def test_event_form_view_without_login(self):
        """Test que verifica que la vista event_form redirige a login cuando el usuario no está logueado"""
        # Hacer petición a la vista event_form sin login
        response = self.client.get(reverse("event_form"))

        # Verificar que redirecciona al login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

    def test_event_form_edit_existing(self):
        """Test que verifica que se puede editar un evento existente"""
        # Login con usuario organizador
        self.client.login(username="organizador", password="password123")

        # Hacer petición a la vista event_form para editar evento existente
        response = self.client.get(reverse("event_edit", args=[self.event1.id]))

        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/event_form.html")
        self.assertEqual(response.context["event"].id, self.event1.id)


class EventFormSubmissionTest(BaseEventTestCase):
    """Tests para la creación y edición de eventos mediante POST"""

    def test_event_form_post_create(self):
        """Test que verifica que se puede crear un evento mediante POST"""
        # Login con usuario organizador
        self.client.login(username="organizador", password="password123")

        # Crear datos para el evento
        event_data = {
            "title": "Nuevo Evento",
            "description": "Descripción del nuevo evento",
            "date": "2025-05-01",
            "time": "14:30",
        }

        # Hacer petición POST a la vista event_form
        response = self.client.post(reverse("event_form"), event_data)

        # Verificar que redirecciona a events
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("events"))

        # Verificar que se creó el evento
        self.assertTrue(Event.objects.filter(title="Nuevo Evento").exists())
        evento = Event.objects.get(title="Nuevo Evento")
        self.assertEqual(evento.description, "Descripción del nuevo evento")
        self.assertEqual(evento.scheduled_at.year, 2025)
        self.assertEqual(evento.scheduled_at.month, 5)
        self.assertEqual(evento.scheduled_at.day, 1)
        self.assertEqual(evento.scheduled_at.hour, 14)
        self.assertEqual(evento.scheduled_at.minute, 30)
        self.assertEqual(evento.organizer, self.organizer)

    def test_event_form_post_edit(self):
        """Test que verifica que se puede editar un evento existente mediante POST"""
        # Login con usuario organizador
        self.client.login(username="organizador", password="password123")

        # Datos para actualizar el evento
        updated_data = {
            "title": "Evento 1 Actualizado",
            "description": "Nueva descripción actualizada",
            "date": "2025-06-15",
            "time": "16:45",
        }

        # Hacer petición POST para editar el evento
        response = self.client.post(reverse("event_edit", args=[self.event1.id]), updated_data)

        # Verificar que redirecciona a events
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("events"))

        # Verificar que el evento fue actualizado
        self.event1.refresh_from_db()

        self.assertEqual(self.event1.title, "Evento 1 Actualizado")
        self.assertEqual(self.event1.description, "Nueva descripción actualizada")
        self.assertEqual(self.event1.scheduled_at.year, 2025)
        self.assertEqual(self.event1.scheduled_at.month, 6)
        self.assertEqual(self.event1.scheduled_at.day, 15)
        self.assertEqual(self.event1.scheduled_at.hour, 16)
        self.assertEqual(self.event1.scheduled_at.minute, 45)

    def test_notification_creation_on_event_update(self):
        """Test que verifica que se crea una notificación al editar un evento"""
        # Login con usuario organizador
        self.client.login(username="organizador", password="password123")

        # Editamos el evento
        update_event_data = {
            "title": "Evento 1",
            "description": "Descripción del evento 1",
            "date": (timezone.now() + datetime.timedelta(days=1)).date().isoformat(),  # 'YYYY-MM-DD'
            "time": (timezone.now() + datetime.timedelta(days=1)).time().strftime("%H:%M"),  # 'HH:MM'
            "venue": self.venue2.id,  # o simplemente self.venue1.id si el form espera int
        }
        #Formateo la fecha al igual que la vista
        date_str = update_event_data["date"]  # 'YYYY-MM-DD'
        time_str = update_event_data["time"]  # 'HH:MM'

        year, month, day = map(int, date_str.split("-"))
        hour, minute = map(int, time_str.split(":"))

        scheduled_at = timezone.make_aware(
            datetime.datetime(year, month, day, hour, minute)
        )

        # Hacer petición POST a la vista event_form
        url = reverse("event_edit", args=[self.event1.id])
        response = self.client.post(url, update_event_data)
        self.assertRedirects(response, reverse("events"))
        
        #Verificar que los usarios tengan notificaciones
        usuarios = User.objects.filter(tickets__event=self.event1)
        for usuario in usuarios:
            self.assertTrue(
                Notification.objects.filter(
                    users=usuario,
                    message = f"El evento '{self.event1.title}' ha sido actualizado. Fecha: {scheduled_at} y lugar: {self.venue2.name}."
                ).exists()
            )
    
        
       

class EventDeleteViewTest(BaseEventTestCase):
    """Tests para la eliminación de eventos"""

    def test_event_delete_with_organizer(self):
        """Test que verifica que un organizador puede eliminar un evento"""
        # Iniciar sesión como organizador
        self.client.login(username="organizador", password="password123")

        # Verificar que el evento existe antes de eliminar
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())

        # Hacer una petición POST para eliminar el evento
        response = self.client.post(reverse("event_delete", args=[self.event1.id]))

        # Verificar que redirecciona a la página de eventos
        self.assertRedirects(response, reverse("events"))

        # Verificar que el evento ya no existe
        self.assertFalse(Event.objects.filter(pk=self.event1.id).exists())

    def test_event_delete_with_regular_user(self):
        """Test que verifica que un usuario regular no puede eliminar un evento"""
        # Iniciar sesión como usuario regular
        self.client.login(username="regular", password="password123")

        # Verificar que el evento existe antes de intentar eliminarlo
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())

        # Hacer una petición POST para intentar eliminar el evento
        response = self.client.post(reverse("event_delete", args=[self.event1.id]))

        # Verificar que redirecciona a la página de eventos sin eliminar
        self.assertRedirects(response, reverse("events"))

        # Verificar que el evento sigue existiendo
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())

    def test_event_delete_with_get_request(self):
        """Test que verifica que la vista redirecciona si se usa GET en lugar de POST"""
        # Iniciar sesión como organizador
        self.client.login(username="organizador", password="password123")

        # Hacer una petición GET para intentar eliminar el evento
        response = self.client.get(reverse("event_delete", args=[self.event1.id]))

        # Verificar que redirecciona a la página de eventos
        self.assertRedirects(response, reverse("events"))

        # Verificar que el evento sigue existiendo
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())

    def test_event_delete_nonexistent_event(self):
        """Test que verifica el comportamiento al intentar eliminar un evento inexistente"""
        # Iniciar sesión como organizador
        self.client.login(username="organizador", password="password123")

        # ID inexistente
        nonexistent_id = 9999

        # Verificar que el evento con ese ID no existe
        self.assertFalse(Event.objects.filter(pk=nonexistent_id).exists())

        # Hacer una petición POST para eliminar el evento inexistente
        response = self.client.post(reverse("event_delete", args=[nonexistent_id]))

        # Verificar que devuelve error 404
        self.assertEqual(response.status_code, 404)

    def test_event_delete_without_login(self):
        """Test que verifica que la vista redirecciona a login si el usuario no está autenticado"""
        # Verificar que el evento existe antes de intentar eliminarlo
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())

        # Hacer una petición POST sin iniciar sesión
        response = self.client.post(reverse("event_delete", args=[self.event1.id]))

        # Verificar que redirecciona al login
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))

        # Verificar que el evento sigue existiendo
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())

    def test_toggle_favorite_view(self):
        """Test que verifica la vista de toggle_favorite"""
        # Login como usuario regular
        self.client.login(username="regular", password="password123")
        
        # Intentar marcar un evento como favorito
        response = self.client.get(f'/events/{self.event1.id}/toggle-favorite/')
        self.assertEqual(response.status_code, 302)  # Redirección
        
        # Verificar que el evento fue agregado a favoritos
        self.assertTrue(self.event1.favorited_by.filter(id=self.regular_user.id).exists())
        
        # Intentar quitar el evento de favoritos
        response = self.client.get(f'/events/{self.event1.id}/toggle-favorite/')
        self.assertEqual(response.status_code, 302)  # Redirección
        
        # Verificar que el evento fue quitado de favoritos
        self.assertFalse(self.event1.favorited_by.filter(id=self.regular_user.id).exists())

    def test_favorite_button_not_visible_for_organizer(self):
        """Test que verifica que el botón de favorito no es visible para organizadores"""
        # Login como organizador
        self.client.login(username="organizador", password="password123")
        
        # Obtener la página de eventos
        response = self.client.get('/events/')
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el botón de favorito no está en la respuesta
        self.assertNotContains(response, 'toggle-favorite')
        
    def test_event_reprograms_when_date_changes(self):
        new_date = (timezone.now() + datetime.timedelta(days=5)).date().strftime('%Y-%m-%d')
        new_time = '15:00'

        response = self.client.post(reverse('event_edit', args=[self.event_id]), {
            'title': self.event.title,
            'description': self.event.description,
            'date': new_date,
            'time': new_time,
            'venue': str(self.venue_id),
            'categories': [self.category.id]
        })

        self.event.refresh_from_db()
        self.assertEqual(self.event.state, Event.REPROGRAMED)

    def test_event_canceled_view_sets_state_correctly(self):
        response = self.client.post(reverse('event_canceled', args=[self.event_id]))
        self.event.refresh_from_db()
        self.assertEqual(self.event.state, Event.CANCELED)
