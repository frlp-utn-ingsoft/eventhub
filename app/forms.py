from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
import re
from .models import Ticket, Event, PaymentInfo

class EventForm(forms.ModelForm):
    scheduled_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Fecha del evento"
    )
    scheduled_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        label="Hora del evento"
    )

    class Meta:
        model = Event
        fields = [
            'title', 
            'description', 
            'general_price', 
            'vip_price', 
            'general_tickets_total', 
            'vip_tickets_total'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        scheduled_date = cleaned_data.get('scheduled_date')
        scheduled_time = cleaned_data.get('scheduled_time')

        if scheduled_date and scheduled_time:
            event_datetime = timezone.make_aware(
                timezone.datetime.combine(scheduled_date, scheduled_time)
            )
            if event_datetime < timezone.now():
                self.add_error('scheduled_date', 'La fecha del evento no puede estar en el pasado')

        general_tickets = cleaned_data.get('general_tickets_total')
        vip_tickets = cleaned_data.get('vip_tickets_total')

        if general_tickets is not None and general_tickets < 0:
            self.add_error('general_tickets_total', 'La cantidad de tickets generales no puede ser negativa')

        if vip_tickets is not None and vip_tickets < 0:
            self.add_error('vip_tickets_total', 'La cantidad de tickets VIP no puede ser negativa')

        if (general_tickets == 0 and vip_tickets == 0):
            self.add_error(None, 'Debe haber al menos un ticket disponible (general o VIP)')

        return cleaned_data

class TicketForm(forms.ModelForm):
    accept_terms = forms.BooleanField(
        required=True,
        label="Acepto los términos y condiciones y la política de privacidad",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Ticket
        fields = ['type', 'quantity']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
            }),
        }

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        ticket_type = cleaned_data.get('type')
        quantity = cleaned_data.get('quantity')

        if not quantity or quantity < 1:
            raise ValidationError({'quantity': 'La cantidad debe ser al menos 1'})

        if ticket_type == Ticket.TicketType.VIP and quantity > 2:
            raise ValidationError({'type': 'Máximo 2 tickets VIP por compra'})

        if self.event and ticket_type:
            available = self.event.get_available_tickets(ticket_type)
            if available < quantity:
                ticket_type_str = ticket_type.lower()
                raise ValidationError({
                    'quantity': f'Solo quedan {available} tickets {ticket_type_str} disponibles'
                })

        return cleaned_data

class PaymentForm(forms.ModelForm):
    expiry_date = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'MM/AA'})
    )

    class Meta:
        model = PaymentInfo  
        fields = ['card_type', 'card_number', 'expiry_date', 'cvv', 'card_holder', 'save_card']
        widgets = {
            'card_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '1234 5678 9012 3456',
                'data-mask': '0000 0000 0000 0000'
            }),
            'cvv': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'CVV',
                'data-mask': '0000'
            }),
            'card_holder': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre como aparece en la tarjeta'
            }),
            'card_type': forms.Select(attrs={'class': 'form-control'})
        }

    def clean_card_number(self):
        card_number = self.cleaned_data['card_number'].replace(' ', '')
        if not card_number.isdigit() or len(card_number) not in (13, 15, 16):
            raise ValidationError('Número de tarjeta inválido')
        return card_number

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data.get('expiry_date', '').strip()
        
        if not expiry_date:
            raise ValidationError('La fecha de expiración es requerida')
        
        if not re.match(r'^(0[1-9]|1[0-2])/\d{2}$', expiry_date):
            raise ValidationError('Formato inválido. Use MM/AA (ej. 12/28)')
        
        try:
            month, year = map(int, expiry_date.split('/'))
            full_year = 2000 + year
            now = timezone.now()
            
            if full_year < now.year or (full_year == now.year and month < now.month):
                raise ValidationError('Tarjeta expirada')
                
            if full_year > now.year + 10:
                raise ValidationError(f'Año inválido. Máximo permitido: {now.year + 10}')
            
            self.cleaned_data['expiry_month'] = month
            self.cleaned_data['expiry_year'] = full_year
            
        except ValueError:
            raise ValidationError('Fecha inválida')
            
        return expiry_date

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.expiry_month = self.cleaned_data.get('expiry_month')
        instance.expiry_year = self.cleaned_data.get('expiry_year')
        if commit:
            instance.save()
        return instance
    
    
class TicketFilterForm(forms.Form):
    FILTER_CHOICES = (
        ('all', 'Todos los tickets'),
        ('upcoming', 'Eventos próximos'),
        ('past', 'Eventos pasados'),
        ('used', 'Tickets usados'),
        ('unused', 'Tickets no usados'),
    )
    filter_by = forms.ChoiceField(
        choices=FILTER_CHOICES,
        required=False,
        initial='all',
        widget=forms.Select(attrs={'class': 'form-control'})
    )