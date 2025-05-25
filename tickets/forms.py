from django import forms

from .models import Ticket


class TicketCompraForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['type', 'quantity']
        error_messages = {
            'type': {
                'required': 'El tipo de entrada es obligatorio.',
            },
            'quantity': {
                'required': 'La cantidad es obligatoria.',
            }
        }

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        
        if quantity is not None:
            if quantity < 1:
                raise forms.ValidationError('La cantidad debe ser mayor a 0.')
            if quantity > 10:
                raise forms.ValidationError('No se pueden comprar más de 10 tickets.')
        
        return cleaned_data


class TicketUpdateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['type', 'quantity']

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        
        if quantity is not None:
            if quantity < 1:
                raise forms.ValidationError('La cantidad debe ser mayor a 0.')
            if quantity > 10:
                raise forms.ValidationError('No se pueden tener más de 10 tickets.')
        
        return cleaned_data