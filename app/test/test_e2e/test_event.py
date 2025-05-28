import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client, TestCase # Importa TestCase
from app.models import Event, Venue

User = get_user_model()

# Envuelve tus funciones de prueba en una clase que herede de django.test.TestCase
class EventCancellationTests(TestCase): # Define una clase de prueba

    def setUp(self):
        # Opcional: Si necesitas crear datos comunes para múltiples tests en esta clase,
        # puedes hacerlo aquí en el método setUp.
        pass

    @pytest.mark.django_db # Este decorador es opcional aquí, ya que TestCase ya maneja la base de datos transaccional.
    def test_cancel_event_as_organizer(self):
        """
        Test completo: Organizador cancela un evento exitosamente.
        Todo en un solo archivo, sin fixtures externos.
        """
        # 1. Crear datos desde cero
        organizer = User.objects.create_user(
            username="organizer",
            email="organizer@test.com",
            password="testpass123",
            is_organizer=True,
        )
        
        venue = Venue.objects.create(
            name="Test Venue",
            adress="123 Test St",
            city="Test City",
            capacity=100,
            contact="test@venue.com",
        )

        event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            scheduled_at="2025-12-31 20:00:00",  # Fecha futura
            organizer=organizer,
            venue=venue,
            state=Event.ACTIVE,  # Estado inicial
        )

        # 2. Cliente HTTP y autenticación
        client = Client()
        client.force_login(organizer)

        # 3. Hacer POST para cancelar
        url = reverse("event_canceled", kwargs={"event_id": event.id})
        response = client.post(url)

        # 4. Verificaciones
        assert response.status_code == 302  # Redirección
        assert response.url == reverse("events")

        updated_event = Event.objects.get(id=event.id)
        assert updated_event.state == Event.CANCELED  # Estado actualizado

    @pytest.mark.django_db # Este decorador es opcional aquí.
    def test_normal_user_cannot_cancel_event(self):
        """
        Test: Usuario normal no puede cancelar eventos.
        """
        # 1. Crear usuarios y evento
        organizer = User.objects.create_user(
            username="organizer_2", # Cambiado para evitar conflicto si se ejecutan ambos tests en la misma db
            email="organizer_2@test.com",
            password="testpass123",
            is_organizer=True,
        )
        
        normal_user = User.objects.create_user(
            username="normaluser",
            email="normal@test.com",
            password="testpass123",
            is_organizer=False,
        )

        venue = Venue.objects.create(
            name="Test Venue 2", # Cambiado para evitar conflicto
            adress="456 Test St",
            city="Test City",
            capacity=100,
            contact="test2@venue.com",
        )

        event = Event.objects.create(
            title="Test Event 2", # Cambiado para evitar conflicto
            description="Test Description 2",
            scheduled_at="2025-12-31 20:00:00",
            organizer=organizer,  # Evento pertenece al organizador
            venue=venue,
            state=Event.ACTIVE,
        )

        # 2. Autenticar usuario normal
        client = Client()
        client.force_login(normal_user)

        # 3. Intentar cancelar (debería fallar)
        url = reverse("event_canceled", kwargs={"event_id": event.id})
        response = client.post(url)

        # 4. Verificaciones
        # Tu vista `event_canceled` redirige si el usuario no es organizador.
        # Si la vista redirige a 'events' sin mostrar un error 403,
        # entonces la aserción debería ser 302 y verificar la URL de redirección.
        # Si quieres un 403, la vista debería retornar un HttpResponseForbidden.
        # Basado en tu views.py:
        # if not user.is_organizer: return redirect("events")
        # Esto significa que siempre redirigirá para usuarios no organizadores.
        assert response.status_code == 302  # Redirección
        assert response.url == reverse("events") # Redirige a la lista de eventos

        updated_event = Event.objects.get(id=event.id)
        assert updated_event.state == Event.ACTIVE  # Estado NO cambió