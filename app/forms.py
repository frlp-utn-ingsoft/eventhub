from django import forms
from .models import Ticket

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['event', 'user', 'ticket_code', 'quantity', 'type']