#  test_event_status_integration.py  (o puedes agregarlo a test_event.py)
import datetime

from django.urls import reverse
from django.utils import timezone

from app.models import Event, Venue
from app.test.test_integration.test_event import BaseEventTestCase  #  Reutilizamos la clase base


class EventStatusIntegrationTest(BaseEventTestCase):
    """Tests de integración para el estado del evento"""

    def setUp(self):
        super().setUp()
        #  Crear un lugar para los eventos (necesario para algunos estados)
        self.venue = Venue.objects.create(
            name="Test Venue",
            address="Test Address",
            city="Test City",
            capacity=100,
            contact_info="Test Info",
            created_by=self.organizer,
        )

    def test_event_detail_view_updates_status(self):
        """
        Test que verifica que la vista event_detail actualiza el estado del evento
        al ser accedida.
        """

        #  1.  Crear un evento con fecha en el futuro (estado inicial: 'activo')
        future_event = Event.objects.create(
            title="Future Event",
            description="Event in the future",
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
        )

        #  2.  Acceder a la vista de detalle del evento
        url = reverse("event_detail", args=[future_event.id])
        self.client.login(username="regular", password="password123")  #  Necesitamos estar logueados
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        #  3.  Verificar que el estado del evento se ha actualizado (aunque no debería cambiar en este caso)
        updated_event = Event.objects.get(id=future_event.id)  #  Obtener el evento actualizado de la DB
        self.assertEqual(updated_event.status, "activo")

        #  4.  Modificar la fecha del evento para que sea en el pasado
        future_event.scheduled_at = timezone.now() - timezone.timedelta(days=1)
        future_event.save()

        #  5.  Volver a acceder a la vista de detalle
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        #  6.  Verificar que el estado se ha actualizado a 'finalizado'
        updated_event = Event.objects.get(id=future_event.id)
        self.assertEqual(updated_event.status, "finalizado")

    def test_event_detail_view_status_agotado(self):
        """
        Test que verifica que la vista event_detail actualiza el estado a 'agotado'
        cuando se venden todas las entradas.
        """
        event = Event.objects.create(
            title="Agotado Event",
            description="Event that sells out",
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
            tickets_sold=self.venue.capacity,  # Vender todas las entradas
        )

        url = reverse("event_detail", args=[event.id])
        self.client.login(username="regular", password="password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        updated_event = Event.objects.get(id=event.id)
        self.assertEqual(updated_event.status, "agotado")

    def test_event_detail_view_status_activo(self):
        """
        Test que verifica que la vista event_detail mantiene el estado 'activo'
        para un evento futuro con entradas disponibles.
        """
        event = Event.objects.create(
            title="Activo Event",
            description="Future event",
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
            tickets_sold=0,
        )

        url = reverse("event_detail", args=[event.id])
        self.client.login(username="regular", password="password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        updated_event = Event.objects.get(id=event.id)
        self.assertEqual(updated_event.status, "activo")

    #  Opcional: Test para 'cancelado' o 'reprogramado' si tienes flujos para eso
    #  en la vista o en la lógica de negocio.