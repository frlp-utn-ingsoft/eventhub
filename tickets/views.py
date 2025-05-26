from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from app.models import Event

from .forms import TicketCompraForm, TicketUpdateForm
from .models import Ticket


@login_required
def compra(request, id):
    if not request.user.is_organizer:
        """Vista para mostrar y procesar el formulario de compra de tickets"""
        event = get_object_or_404(Event, id=id)
        
        if request.method == 'POST':
            form = TicketCompraForm(request.POST, user=request.user, event=event)
            if form.is_valid():
                try:
                    # Crear el ticket - el ticket_code se generará automáticamente en el método save()
                    ticket = form.save(commit=False)
                    ticket.user = request.user
                    ticket.event = event
                    ticket.save()
                    
                    # Redirigir a página de confirmación
                    return redirect("events")
                    
                except Exception as e:
                    print(e)
                    messages.error(request, 'Error al procesar la compra.')
                    return render(request, 'tickets/compra.html', {
                        'event': event,
                        'form': form, 
                    })
            else:
                # Si hay errores de validación, mostrar mensajes
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, error)  # type: ignore
                return render(request, 'tickets/compra.html', {
                    'event': event,
                    'form': form,  
                })
        
        # Si es GET, mostrar formulario
        form = TicketCompraForm(user=request.user, event=event)
        return render(request, 'tickets/compra.html', {
            'event': event,
            'form': form,
        })
    else:
        return redirect(reverse('events'))
    
def eliminacion(request):
    """Vista para mostrar tickets y datos del usuario asociado"""
    if request.user.is_organizer:
        if request.method == 'POST':
            ticket_id = request.POST.get('ticket_code')
            if ticket_id:
                Ticket.objects.filter(ticket_code=ticket_id).delete() #vincular funcion en el front
            return redirect(reverse('tickets:eliminacion')) #redireccionar a la misma vista para mostrar los tickets restantes
        if request.method == 'GET':
            tickets= [
                {
                    'ticket_code': ticket.ticket_code,
                    'usuario': ticket.user.email,
                    'evento': ticket.event.title,
                    'quantity': ticket.quantity,
                    'type': ticket.type
                }
                for ticket in Ticket.objects.select_related('user', 'event').all()
            ]
            return render(request, 'tickets/eliminacion.html', {'tickets': tickets})
    else:
        return redirect(reverse('home'))
    
def actualizacion(request, id):
    if not request.user.is_organizer:    
        event = get_object_or_404(Event, id=id)
        
        #metodo GET: Mostrar formulario para editar entradas
        if request.method == 'GET':
            user_tickets = Ticket.objects.filter(event=event, user=request.user)
            return render(request, 'tickets/editar.html', {'event': event, 'user_tickets': user_tickets})
        
        #metodo POST: Actualizar o eliminar entradas
        elif request.method == 'POST':
            action = request.POST.get('action', 'update')
            
            #si es una solicitud de eliminación
            if action == 'delete':
                ticket_id = request.POST.get('ticket_id')
                if ticket_id:
                    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
                    ticket.delete()
            # actualización normal
            else:
                #procesamos cada entrada en el formulario
                for key in request.POST:
                    if key.startswith('ticket_id_'):
                        index = key.split('_')[-1]
                        ticket_id = request.POST.get(key)
                        cantidad = request.POST.get(f'cantidad_{index}', 1)
                        tipo_entrada = request.POST.get(f'tipoEntrada_{index}', 'GENERAL')
                        
                        # Validar con form antes de actualizar
                        form_data = {
                            'type': tipo_entrada,
                            'quantity': cantidad
                        }
                        form = TicketUpdateForm(form_data)
                        
                        if form.is_valid():
                            #actualizo
                            ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
                            ticket.quantity = form.cleaned_data['quantity']
                            ticket.type = form.cleaned_data['type']
                            ticket.save()
                        else:
                            # Si hay errores, mostrar mensajes
                            for field, errors in form.errors.items():
                                for error in errors:
                                    messages.error(request, f'Ticket {ticket_id}: {error}')
            return redirect('tickets:actualizacion', id=id)
    else:
        return redirect(reverse('home'))