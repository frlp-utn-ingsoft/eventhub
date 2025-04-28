from django import forms
from .models import Ticket

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['quantity', 'type']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1}),  
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if not quantity or quantity <= 0:
            raise forms.ValidationError("La cantidad debe ser un número mayor a cero")
        return quantity
