from django import forms
from .models import Ticket

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['quantity', 'type']
        
    # Campos para la simulación de pago con tarjeta (no se guardan en la BD)
    card_number = forms.CharField(max_length=16, required=True, label='Número de Tarjeta')
    card_holder = forms.CharField(max_length=100, required=True, label='Nombre del Titular')
    expiration_date = forms.CharField(max_length=5, required=True, label='Fecha de Expiración (MM/YY)')
    cvc = forms.CharField(max_length=3, required=True, label='CVC')