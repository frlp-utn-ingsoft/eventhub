from django import forms
from .models import Ticket

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['ticket_code', 'quantity', 'type']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Configura el campo 'quantity'
        self.fields['quantity'].widget.attrs.update({
            'class': 'form-control text-center',
            'min': '1',
            'id': 'id_quantity',  
            'inputmode': 'numeric'
        })

        # Setea 'GENERAL' como opción por defecto
        self.fields['type'].initial = 'GENERAL'

        # Aplica clase Bootstrap al select
        self.fields['type'].widget.attrs.update({
            'class': 'form-select'
    })



