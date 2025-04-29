from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from app.models import Event

# Create your views here.

@login_required #decorador para requerir autenticacion
def tickets(request,id):
    event = get_object_or_404(Event, id=id)
    return render(request, "tickets/compra.html", {'event': event}) 