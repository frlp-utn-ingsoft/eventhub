from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from app.models import Event

from .models import Ticket

# Create your views here.

# @login_required #decorador para requerir autenticacion
# def tickets(request,id):
#     event = get_object_or_404(Event, id=id)
#     return render(request, "tickets/compra.html", {'event': event}) 

@login_required
def compra(request, id):
    """Vista para mostrar y procesar el formulario de compra de tickets"""
    event = get_object_or_404(Event, id=id)
    
    if request.method == 'POST':
        # Obtener datos del formulario
        print(request.POST)
        tipo_entrada = request.POST.get('tipoEntrada')
        cantidad = int(request.POST.get('cantidad'))
        
        # Datos de la tarjeta (en un caso real, estos se procesarían con un gateway de pago)
        card_number = request.POST.get('card_number')
        expiry_date = request.POST.get('expiry_date')
        cvv = request.POST.get('cvv')
        card_name = request.POST.get('card_name')
        
        # Validaciones básicas
        if not all([tipo_entrada, cantidad, card_number, expiry_date, cvv, card_name]):
            messages.error(request, 'Por favor complete todos los campos')
            return render(request, 'tickets/compra.html', {'event': event})
            
        try:
            # Crear el ticket - el ticket_code se generará automáticamente en el método save()
            ticket = Ticket(
                user=request.user,
                event=event,
                quantity=cantidad,
                type=tipo_entrada
            )
            ticket.save()
            
            # Redirigir a página de confirmación
            return redirect("home")
            
        except Exception as e:
            print(e)
            return render(request, 'tickets/compra.html', {'event': event})
    
    # Si es GET, mostrar formulario
    return render(request, 'tickets/compra.html', {'event': event})

