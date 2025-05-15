import re
from django import forms
from .models import Ticket
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from datetime import datetime

class TicketForm(forms.ModelForm):
    card_number = forms.CharField(max_length=16, min_length=16, label="Número de tarjeta", validators=[RegexValidator(r'^\d{16}$', message="Debe contener exactamente 16 dígitos numéricos.")],
    )
    card_cvv = forms.CharField(max_length=4, label="CVV", validators=[RegexValidator(r'^\d{3,4}$', message="Debe tener 3 o 4 dígitos numéricos.")],)

    # Select para mes (01 a 12)
    MONTH_CHOICES = [(f"{i:02}", f"{i:02}") for i in range(1, 13)]
    expiry_month = forms.ChoiceField(choices=MONTH_CHOICES, label="Mes de vencimiento")

    # Select para año (desde el actual hasta +10 años)
    current_year = datetime.now().year
    YEAR_CHOICES = [(str(y)[-2:], str(y)) for y in range(current_year, current_year + 21)]
    expiry_year = forms.ChoiceField(choices=YEAR_CHOICES)
    
    quantity = forms.IntegerField(
        min_value=1,
        label="Cantidad de entradas"
    )

    class Meta:
        model = Ticket
        fields = ['event', 'quantity', 'type', 'card_type']  # user y ticket_code se manejan automáticamente
        labels = {
            'event': 'Evento',
            'type': 'Tipo de entrada',
            'card_type': 'Tipo de tarjeta',
        }

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk:
            month = cleaned_data.get('expiry_month')
            year = cleaned_data.get('expiry_year')

            if month and year:
                # Validamos si la tarjeta está vencida
                now = datetime.now()
                exp_year = int('20' + year)
                exp_month = int(month)
                exp_date = datetime(exp_year, exp_month, 1)

                if exp_date.replace(day=28) < now.replace(day=1):
                    self.add_error('expiry_month', 'La tarjeta ya está vencida.')
    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si estamos editando (el ticket ya existe), deshabilitamos algunos campos
        if self.instance and self.instance.pk:
            masked = '************' + self.instance.last4_card_number
            self.fields['card_number'].initial = masked
            self.fields['card_number'].disabled = True
            self.fields['card_number'].validators.clear()

            self.fields['event'].disabled = True
            self.fields['card_type'].disabled = True

            self.fields.pop('card_cvv', None)
            self.fields.pop('expiry_month', None)
            self.fields.pop('expiry_year', None)