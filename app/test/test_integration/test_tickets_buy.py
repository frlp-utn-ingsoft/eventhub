from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import Event, User
from tickets.models import Ticket


class TicketSimpleIntegrationTest(TestCase):

    def setUp(self):
        """
        Configuración mínima: se crea un usuario y un evento para usar en los tests.
        """
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.event = Event.objects.create(
            title='Evento de Prueba',
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            organizer=self.user
        )
        self.client.login(username='testuser', password='password123')

    def test_falla_si_intenta_comprar_mas_de_4_entradas_en_total(self):
        """
        Verifica que el sistema bloquea una compra si el total de entradas supera 4.
        """
        # 1. Estado inicial: El usuario ya tiene 3 entradas.
        Ticket.objects.create(user=self.user, event=self.event, quantity=3)

        # 2. Acción: Intenta comprar 2 entradas más.
        response = self.client.post(
            reverse('tickets:compra', args=[self.event.id]), # type: ignore
            {'type': 'General', 'quantity': 2}
        )

        # 3. Resultado: Se muestra un error y no se crea el ticket.
        form = response.context.get('form')
        self.assertIsNotNone(form) # Asegurarse que el form está en el contexto
        self.assertIn('__all__', form.errors) # type: ignore # Verificar que hay un error global en el form
        self.assertEqual(
            Ticket.objects.get(user=self.user, event=self.event).quantity, 3 # La cantidad no cambió
        )

    def test_permite_multiples_compras_hasta_el_limite_de_4(self):
        """
        Verifica que el sistema permite una segunda compra si el total llega exactamente a 4.
        """
        # 1. Estado inicial: El usuario ya tiene 2 entradas.
        Ticket.objects.create(user=self.user, event=self.event, quantity=2)

        # 2. Acción: Intenta comprar 2 entradas más para llegar al límite.
        response = self.client.post(
            reverse('tickets:compra', args=[self.event.id]), # type: ignore
            {'type': 'VIP', 'quantity': 2}
        )

        # 3. Resultado: La compra es exitosa y el total de entradas es 4.
        self.assertRedirects(response, reverse('events'))
        total_quantity = sum(t.quantity for t in Ticket.objects.filter(user=self.user, event=self.event))
        self.assertEqual(total_quantity, 4)

    def test_falla_actualizacion_si_supera_limite_total(self):
        """
        Verifica que el sistema bloquea una actualización si el total supera 4 entradas.
        """
        # 1. Estado inicial: Usuario tiene 2 tickets separados
        ticket1 = Ticket.objects.create(user=self.user, event=self.event, quantity=2)
        Ticket.objects.create(user=self.user, event=self.event, quantity=1)

        # 2. Acción: Intenta actualizar el primer ticket a 4 (total sería 5)
        response = self.client.post(
            reverse('tickets:actualizacion', args=[self.event.id]), # type: ignore
            {
                'ticket_id_0': ticket1.id, # type: ignore
                'cantidad_0': 4,
                'tipoEntrada_0': 'General'
            }
        )

        # 3. Resultado: Redirecciona pero el ticket no se actualiza
        self.assertRedirects(response, reverse('tickets:actualizacion', args=[self.event.id])) # type: ignore
        ticket1.refresh_from_db()
        self.assertEqual(ticket1.quantity, 2)
        
    def test_permite_actualizacion_dentro_del_limite(self):
        """
        Verifica que el sistema permite actualizar si se mantiene dentro del límite.
        """
        # 1. Estado inicial: Usuario tiene 2 tickets separados
        ticket1 = Ticket.objects.create(user=self.user, event=self.event, quantity=2)
        Ticket.objects.create(user=self.user, event=self.event, quantity=1)

        # 2. Acción: Actualiza el primer ticket a 3 (total sería 4)
        response = self.client.post(
            reverse('tickets:actualizacion', args=[self.event.id]), # type: ignore
            {
                'ticket_id_0': ticket1.id, # type: ignore
                'cantidad_0': 3,
                'tipoEntrada_0': 'VIP'
            }
        )

        # 3. Resultado: La actualización es exitosa
        self.assertRedirects(response, reverse('tickets:actualizacion', args=[self.event.id])) # type: ignore
        ticket1.refresh_from_db()
        self.assertEqual(ticket1.quantity, 3)
        self.assertEqual(ticket1.type, 'VIP')
        
        # Verificar que el total es 4
        total_quantity = sum(t.quantity for t in Ticket.objects.filter(user=self.user, event=self.event))
        self.assertEqual(total_quantity, 4)
        
        # 4. Verificar que la respuesta es exitosa (status 302 por el redirect)
        self.assertEqual(response.status_code, 302)
        
