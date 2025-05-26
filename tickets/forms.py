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

    def __init__(self, *args, user=None, event=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.event = event

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')

        if quantity is None:
            return cleaned_data

        if quantity < 1:
            raise forms.ValidationError('La cantidad debe ser mayor a 0.')

        if quantity > 4:
            raise forms.ValidationError('No se pueden comprar más de 4 tickets por compra.')

        user = self.user
        event = self.event

        if user and event:
            entradas_actuales = sum(
                ticket.quantity for ticket in Ticket.objects.filter(user=user, event=event)
            )
            total_entradas = entradas_actuales + quantity

            if total_entradas > 4:
                raise forms.ValidationError(
                    f'Ya tienes {entradas_actuales} entradas. No puedes superar las 4 por evento.'
                )

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
            if quantity > 4:
                raise forms.ValidationError('No se pueden tener más de 4 tickets.')
        
        return cleaned_data