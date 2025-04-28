from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your views here.

@login_required #decorador para requerir autenticacion
def tickets(request):
    return render(request, "tickets/compra.html")