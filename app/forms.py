from django import forms
from .models import Ticket

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['quantity', 'type']  # Solo lo que el usuario ve y completa

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['quantity'].widget.attrs.update({
            'class': 'form-control text-center',
            'min': '1',
            'id': 'id_quantity',
            'inputmode': 'numeric'
        })

        self.fields['type'].initial = 'GENERAL'
        self.fields['type'].widget.attrs.update({
            'class': 'form-select'
        })


