import time 
from django.urls import reverse
from datetime import date, time, timedelta
import datetime
from django.test import TestCase, Client
from django.utils import timezone
from app.forms import EventForm
from app.models import Event, User, Venue, Category


class BaseEventTestCase(TestCase):
    """Clase base con la configuración común para todos los tests de eventos"""

    def setUp(self):
        # Crear un usuario organizador
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )

        # Crear un usuario regular
        self.regular_user = User.objects.create_user(
            username="regular",
            email="regular@test.com",
            password="password123",
            is_organizer=False,
        )

        # CREA OBJETOS VENUE Y CATEGORY
        self.venue = Venue.objects.create(
            name="Auditorio Test",
            address="Calle Falsa 123",
            capacity=100
        )
        self.category1 = Category.objects.create(name="Música")
        self.category2 = Category.objects.create(name="Conferencia")


        # Crear algunos eventos de prueba
        self.event1 = Event.objects.create(
            title="Evento 1",
            description="Descripción del evento 1",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
        )
        self.event1.categories.add(self.category1) # Asignar categoría al evento existente

        self.event2 = Event.objects.create(
            title="Evento 2",
            description="Descripción del evento 2",
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            organizer=self.organizer,
            venue=self.venue,
        )
        self.event2.categories.add(self.category2) # Asignar categoría al evento existente


        # Cliente para hacer peticiones
        self.client = Client()



class EventsListViewTest(BaseEventTestCase):
    """Tests para la vista de listado de eventos"""

    def test_events_view_with_login(self):
        """Test que verifica que la vista events funciona cuando el usuario está logueado"""
        self.client.login(username="regular", password="password123")
        response = self.client.get(reverse("events"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/events.html")
        self.assertIn("events", response.context)
        self.assertIn("user_is_organizer", response.context)
        self.assertEqual(len(response.context["events"]), 2)
        self.assertFalse(response.context["user_is_organizer"])
        events = list(response.context["events"])
        self.assertEqual(events[0].id, self.event1.id) #type: ignore
        self.assertEqual(events[1].id, self.event2.id) #type: ignore

    def test_events_view_with_organizer_login(self):
        """Test que verifica que la vista events funciona cuando el usuario es organizador"""
        self.client.login(username="organizador", password="password123")
        response = self.client.get(reverse("events"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["user_is_organizer"])

    def test_events_view_without_login(self):
        """Test que verifica que la vista events redirige a login cuando el usuario no está logueado"""
        response = self.client.get(reverse("events"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/")) #type: ignore


class EventDetailViewTest(BaseEventTestCase):
    """Tests para la vista de detalle de un evento"""

    def test_event_detail_view_with_login(self):
        """Test que verifica que la vista event_detail funciona cuando el usuario está logueado"""
        self.client.login(username="regular", password="password123")
        response = self.client.get(reverse("event_detail", args=[self.event1.id]))#type: ignore
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/event_detail.html")
        self.assertIn("event", response.context)
        self.assertEqual(response.context["event"].id, self.event1.id)#type: ignore

    def test_event_detail_view_without_login(self):
        """Test que verifica que la vista event_detail redirige a login cuando el usuario no está logueado"""
        response = self.client.get(reverse("event_detail", args=[self.event1.id]))#type: ignore
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))#type: ignore

    def test_event_detail_view_with_invalid_id(self):
        """Test que verifica que la vista event_detail devuelve 404 cuando el evento no existe"""
        self.client.login(username="regular", password="password123")
        response = self.client.get(reverse("event_detail", args=[999]))
        self.assertEqual(response.status_code, 404)

class EventFormViewTest(BaseEventTestCase):
    """Tests para la vista del formulario de eventos (GET requests)"""

    def test_event_form_view_with_organizer(self):
        """Test que verifica que la vista event_form funciona cuando el usuario es organizador"""
        self.client.login(username="organizador", password="password123")
        response = self.client.get(reverse("event_form"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/event_form.html")
        self.assertIn("form", response.context) 
        self.assertTrue(response.context["user_is_organizer"])

    def test_event_form_view_with_regular_user(self):
        """Test que verifica que la vista event_form redirige cuando el usuario no es organizador"""
        self.client.login(username="regular", password="password123")
        response = self.client.get(reverse("event_form"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("events"))#type: ignore

    def test_event_form_view_without_login(self):
        """Test que verifica que la vista event_form redirige a login cuando el usuario no está logueado"""
        response = self.client.get(reverse("event_form"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))#type: ignore

    def test_event_form_edit_existing(self):
        """Test que verifica que se puede editar un evento existente"""
        self.client.login(username="organizador", password="password123")
        response = self.client.get(reverse("event_edit", args=[self.event1.id]))#type: ignore
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/event_form.html")
        self.assertIn("form", response.context) 
        # Y la instancia del evento debe estar dentro del formulario
        self.assertIsNotNone(response.context["form"].instance) # Asegurarse de que hay una instancia
        self.assertEqual(response.context["form"].instance.id, self.event1.id) #type: ignore


class EventFormSubmissionTest(BaseEventTestCase):
    """Tests para la creación y edición de eventos mediante POST (a través de formularios)"""

    def test_event_form_post_create(self):
        """Test que verifica que se puede crear un evento mediante POST usando el formulario."""
        self.client.login(username="organizador", password="password123")

        # Define una fecha en el futuro para el evento
        # Se asegura de que sea un objeto date, y luego lo formatea para el POST
        future_date_obj = timezone.localdate() + datetime.timedelta(days=7) 
        future_date_str = future_date_obj.strftime('%Y-%m-%d')
        
        # Define la hora de forma naive, como la recibiría el formulario
        test_time_naive = datetime.time(14, 30) 
        
        event_data = {
            "title": "Nuevo Evento Via Form",
            "description": "Descripción del nuevo evento via formulario",
            "date": future_date_str,
            "time": test_time_naive.strftime('%H:%M'), # Formatea la hora para el POST
            "categories": [self.category1.id, self.category2.id],#type: ignore
            "venue": self.venue.id,#type: ignore
        }

        initial_event_count = Event.objects.count()

        response = self.client.post(reverse("event_form"), event_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("events"))#type: ignore

        self.assertEqual(Event.objects.count(), initial_event_count + 1)
        
        new_event = Event.objects.get(title="Nuevo Evento Via Form") 
        
        self.assertEqual(new_event.description, "Descripción del nuevo evento via formulario")
        self.assertEqual(new_event.scheduled_at.date(), future_date_obj) # Compara directamente con el objeto date
        
      
        local_scheduled_time = timezone.localtime(new_event.scheduled_at).time()
        
        self.assertEqual(local_scheduled_time.hour, test_time_naive.hour)
        self.assertEqual(local_scheduled_time.minute, test_time_naive.minute)
        self.assertEqual(new_event.organizer, self.organizer) 
        self.assertEqual(new_event.venue, self.venue)
        self.assertIn(self.category1, new_event.categories.all())
        self.assertIn(self.category2, new_event.categories.all())


    def test_event_form_post_edit(self):
        """Test que verifica que se puede editar un evento existente mediante POST usando el formulario."""
        self.client.login(username="organizador", password="password123")

        # Define una fecha en el futuro para el evento
        # Se asegura de que sea un objeto date, y luego lo formatea para el POST
        future_date_obj = timezone.localdate() + datetime.timedelta(days=10)
        future_date_str = future_date_obj.strftime('%Y-%m-%d')
        
        # Define la hora de forma naive, como la recibiría el formulario
        test_time_naive = datetime.time(16, 45) # La hora que esperas enviar y ver en la zona horaria local

        updated_data = {
            "title": "Evento 1 Actualizado Via Form", 
            "description": "Nueva descripción actualizada via formulario",
            "date": future_date_str,
            "time": test_time_naive.strftime('%H:%M'), # Formatea la hora para el POST
            "categories": [self.category2.id], #type: ignore
            "venue": self.venue.id, #type: ignore
        }

        response = self.client.post(reverse("event_edit", args=[self.event1.id]), updated_data) #type: ignore

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("events")) #type: ignore

        self.event1.refresh_from_db()

        self.assertEqual(self.event1.title, "Evento 1 Actualizado Via Form")
        self.assertEqual(self.event1.description, "Nueva descripción actualizada via formulario")
        self.assertEqual(self.event1.scheduled_at.date(), future_date_obj)
  
        local_scheduled_time = timezone.localtime(self.event1.scheduled_at).time()
        
        self.assertEqual(local_scheduled_time.hour, test_time_naive.hour)
        self.assertEqual(local_scheduled_time.minute, test_time_naive.minute)

        self.assertEqual(self.event1.organizer, self.organizer) 
        self.assertEqual(self.event1.venue, self.venue)
        self.assertIn(self.category2, self.event1.categories.all())
        self.assertNotIn(self.category1, self.event1.categories.all())

class EventDeleteViewTest(BaseEventTestCase):
    """Tests para la eliminación de eventos"""

    def test_event_delete_with_organizer(self):
        """Test que verifica que un organizador puede eliminar un evento"""
        self.client.login(username="organizador", password="password123")
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())#type: ignore
        response = self.client.post(reverse("event_delete", args=[self.event1.id]))#type: ignore
        self.assertRedirects(response, reverse("events"))
        self.assertFalse(Event.objects.filter(pk=self.event1.id).exists())#type: ignore

    def test_event_delete_with_regular_user(self):
        """Test que verifica que un usuario regular no puede eliminar un evento"""
        self.client.login(username="regular", password="password123")
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())#type: ignore
        response = self.client.post(reverse("event_delete", args=[self.event1.id]))#type: ignore
        self.assertRedirects(response, reverse("events"))
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())#type: ignore

    def test_event_delete_with_get_request(self):
        """Test que verifica que la vista redirecciona si se usa GET en lugar de POST"""
        self.client.login(username="organizador", password="password123")
        response = self.client.get(reverse("event_delete", args=[self.event1.id]))#type: ignore
        self.assertRedirects(response, reverse("events"))
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())#type: ignore

    def test_event_delete_nonexistent_event(self):
        """Test que verifica el comportamiento al intentar eliminar un evento inexistente"""
        self.client.login(username="organizador", password="password123")
        nonexistent_id = 9999
        self.assertFalse(Event.objects.filter(pk=nonexistent_id).exists())
        response = self.client.post(reverse("event_delete", args=[nonexistent_id]))
        self.assertEqual(response.status_code, 404)

    def test_event_delete_without_login(self):
        """Test que verifica que la vista redirecciona a login si el usuario no está autenticado"""
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())#type: ignore
        response = self.client.post(reverse("event_delete", args=[self.event1.id]))#type: ignore
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/"))#type: ignore
        self.assertTrue(Event.objects.filter(pk=self.event1.id).exists())#type: ignore
