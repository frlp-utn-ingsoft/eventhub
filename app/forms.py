from django import forms
from .models import Ticket
from .models import Event
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from datetime import datetime

class TicketForm(forms.ModelForm):
    card_number = forms.CharField(
        max_length=16, 
        min_length=16, 
        label="Número de tarjeta", 
        validators=[RegexValidator(r'^\d{16}$', message="Debe contener exactamente 16 dígitos numéricos.")],
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    card_cvv = forms.CharField(
        max_length=4, 
        label="CVV", 
        validators=[RegexValidator(r'^\d{3,4}$', message="Debe tener 3 o 4 dígitos numéricos.")],
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    MONTH_CHOICES = [(f"{i:02}", f"{i:02}") for i in range(1, 13)]
    expiry_month = forms.ChoiceField(
        choices=MONTH_CHOICES, 
        label="Mes",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    current_year = datetime.now().year
    YEAR_CHOICES = [(str(y)[-2:], str(y)) for y in range(current_year, current_year + 21)]
    expiry_year = forms.ChoiceField(
        choices=YEAR_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    quantity = forms.IntegerField(
        min_value=1,
        label="Cantidad de entradas",
        widget=forms.NumberInput(attrs={'id': 'id_quantity', 'class': 'form-control'})
    )

    TYPE_CHOICES = [
        ('', 'Seleccione un tipo de entrada'),
        ('general', 'General'),
        ('vip', 'VIP'),
    ]

    type = forms.ChoiceField(
        choices=TYPE_CHOICES, 
        required=True, 
        label="Tipo de entrada", 
        widget=forms.Select(attrs={
            'id': 'id_type',
            'class': 'form-control'
        })
    )

    def clean_type(self):
        value = self.cleaned_data['type']
        if value == '':
            raise forms.ValidationError('Debe seleccionar un tipo de entrada.')
        return value

    class Meta:
        model = Ticket
        fields = ['event', 'quantity', 'type', 'card_type']
        labels = {
            'event': 'Evento',
            'type': 'Tipo de entrada',
            'card_type': 'Tipo de tarjeta',
        }
        widgets = {
            'event': forms.Select(attrs={'class': 'form-control'}),
            'card_type': forms.Select(attrs={'class': 'form-control'})
        }

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk:
            month = cleaned_data.get('expiry_month')
            year = cleaned_data.get('expiry_year')

            if month and year:
                now = datetime.now()
                exp_year = int('20' + year)
                exp_month = int(month)
                exp_date = datetime(exp_year, exp_month, 1)

                if exp_date.replace(day=28) < now.replace(day=1):
                    self.add_error('expiry_month', 'La tarjeta ya está vencida.')
    

    def __init__(self, *args,  fixed_event=False, event_instance=None, **kwargs):
        super().__init__(*args, **kwargs)

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

        if fixed_event and event_instance:
            self.fields.pop('event')
            self.event_instance = event_instance
        else:
            self.event_instance = None


class TicketFilterForm(forms.Form):
    event = forms.ModelChoiceField(queryset=Event.objects.none(), required=False, label="Evento")
    type = forms.ChoiceField(choices=[('', 'Todos'), ('general', 'General'), ('vip', 'VIP')], required=False, label="Tipo de entrada")
    date_from = forms.DateField(required=False, label="Desde", widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, label="Hasta", widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['event'].queryset = Event.objects.filter(organizer=user)