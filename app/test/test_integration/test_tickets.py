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

        response = self.client.post(
            reverse('tickets:compra', args=[self.event.id]), # type: ignore
            {'type': 'General', 'quantity': 5}
        )
        
        form = response.context.get('form')
        self.assertIsNotNone(form) 
        self.assertIn('__all__', form.errors) # type: ignore 
        self.assertFalse(Ticket.objects.filter(user=self.user, event=self.event).exists()) 
        

    def test_permite_compra_hasta_el_limite_de_4(self):
        """
        Verifica que el sistema permite una compra si el total llega exactamente a 4.
        """

        response = self.client.post(
            reverse('tickets:compra', args=[self.event.id]), # type: ignore
            {'type': 'VIP', 'quantity': 4}
        )

        self.assertRedirects(response, reverse('events'))
        total_quantity = sum(t.quantity for t in Ticket.objects.filter(user=self.user, event=self.event))
        self.assertEqual(total_quantity, 4)

    def test_falla_actualizacion_si_supera_limite_total(self):
        """
        Verifica que el sistema bloquea una actualización si el total supera 4 entradas.
        """
        ticket1 = Ticket.objects.create(user=self.user, event=self.event, quantity=2)

        response = self.client.post(
            reverse('tickets:actualizacion', args=[self.event.id]), # type: ignore
            {
                'ticket_id_0': ticket1.id, # type: ignore
                'cantidad_0': 5,
                'tipoEntrada_0': 'General'
            }
        )

        self.assertRedirects(response, reverse('tickets:actualizacion', args=[self.event.id])) # type: ignore
        ticket1.refresh_from_db()
        self.assertEqual(ticket1.quantity, 2)
        
    def test_permite_actualizacion_dentro_del_limite(self):
        """
        Verifica que el sistema permite actualizar si se mantiene dentro del límite.
        """
        ticket1 = Ticket.objects.create(user=self.user, event=self.event, quantity=2)

        response = self.client.post(
            reverse('tickets:actualizacion', args=[self.event.id]), # type: ignore
            {
                'ticket_id_0': ticket1.id, # type: ignore
                'cantidad_0': 3,
                'tipoEntrada_0': 'VIP'
            }
        )


        self.assertRedirects(response, reverse('tickets:actualizacion', args=[self.event.id])) # type: ignore
        ticket1.refresh_from_db()
        self.assertEqual(ticket1.quantity, 3)
        self.assertEqual(ticket1.type, 'VIP')
        

        total_quantity = sum(t.quantity for t in Ticket.objects.filter(user=self.user, event=self.event))
        self.assertEqual(total_quantity, 3)
        

        self.assertEqual(response.status_code, 302)
        
