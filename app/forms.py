from django import forms
from .models import Rating, Venue, Event, Category, Ticket, PaymentInfo, RefundRequest
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone
from datetime import datetime
import re


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['title', 'score', 'comment']

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise forms.ValidationError("El título no puede estar vacío.")
        return title

    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '').strip()
        if not comment:
            raise forms.ValidationError("El comentario no puede estar vacío.")
        return comment

    def clean_score(self):
        score = self.cleaned_data.get('score')
        if not score:
            raise forms.ValidationError("Debe seleccionar una calificación.")
        return score

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'is_active']
        labels = {
            'name': 'Nombre',
            'description': 'Descripción',
            'is_active': 'Activo',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        error_messages = {
            'name': {
                'required': 'Por favor, ingrese un nombre',
            },
            'description': {
                'required': 'Por favor, ingrese una descripción',
            },
        }

    def clean_name(self):
        name = self.cleaned_data.get("name")

        if not name:
            raise forms.ValidationError("El nombre es obligatorio")

        if len(name) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 caracteres")

        if len(name) > 100:
            raise forms.ValidationError("El nombre no puede tener más de 100 caracteres")

        qs = Category.objects.filter(name=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("Ya existe una categoría con ese nombre")

        return name

    def clean_description(self):
        description = self.cleaned_data.get("description")

        if not description:
            raise forms.ValidationError("La descripción es obligatoria")

        if len(description) < 10:
            raise forms.ValidationError("La descripción debe tener al menos 10 caracteres")

        if len(description) > 500:
            raise forms.ValidationError("La descripción no puede tener más de 500 caracteres")

        return description

class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = ['name', 'address', 'city', 'capacity', 'contact']
        labels = {
            'name': 'Nombre de la ubicación',
            'address': 'Dirección',
            'city': 'Ciudad',
            'capacity': 'Capacidad (número de personas)',
            'contact': 'Contacto',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Ej: Estadio Nacional',
                'class': 'form-control',
                'maxlength': '100'
            }),
            'address': forms.TextInput(attrs={
                'placeholder': 'Ej: Av. Grecia 2001',
                'class': 'form-control'
            }),
            'city': forms.TextInput(attrs={
                'placeholder': 'Chile',
                'class': 'form-control',
                'maxlength': '100'
            }),
            'capacity': forms.NumberInput(attrs={
                'placeholder': 'Ej: 1000',
                'class': 'form-control'
            }),
            'contact': forms.Textarea(attrs={
                'placeholder': 'Ej: contacto@email.com o +54 911 12345678',
                'class': 'form-control',
                'rows': 3,
                'maxlength': '100'
            }),
        }

    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')
        if capacity is not None and capacity <= 0:
            raise ValidationError("La capacidad no puede ser cero.")
        return capacity

    def clean_contact(self):
        contact = self.cleaned_data.get('contact', '').strip()

        email_valid = True
        try:
            validate_email(contact)
        except ValidationError:
            email_valid = False

        phone_valid = bool(re.match(r'^\+?\d[\d\s\-\(\)]{7,}$', contact))

        if not (email_valid or phone_valid):
            raise ValidationError("El contacto debe ser un número de teléfono válido o una dirección de email.")
        
        return contact


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
        fields = '__all__' 
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'venue': forms.Select(attrs={'class': 'form-control'}),
            'categories': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        venues = Venue.objects.all()
        if venues.exists():
           
            self.fields['venue'] = forms.ModelChoiceField(
                queryset=venues,
                widget=forms.Select(attrs={'class': 'form-control'})
            )
        else:
           
            self.fields['venue'] = forms.ChoiceField(
                choices=[('', 'No hay ubicaciones disponibles')],
                widget=forms.Select(attrs={
                    'class': 'form-control',
                    'disabled': True
                })
            )

   
    def clean(self):
        cleaned_data = super().clean() or {}
        venue = cleaned_data.get('venue')
        general_tickets = cleaned_data.get('general_tickets_total', 0)
        vip_tickets = cleaned_data.get('vip_tickets_total', 0)
        
        if venue and (general_tickets or vip_tickets):
            total_tickets = general_tickets + vip_tickets
            if total_tickets > venue.capacity:
                raise ValidationError(
                    f"La cantidad total de tickets ({total_tickets}) excede la capacidad del lugar ({venue.capacity})."
                )
        scheduled_date = cleaned_data.get('scheduled_date')
        scheduled_time = cleaned_data.get('scheduled_time')

        if scheduled_date and scheduled_time:
            try:
                event_datetime = timezone.make_aware(
                    datetime.combine(scheduled_date, scheduled_time)
                )
                if event_datetime < timezone.now():
                    self.add_error('scheduled_date', 'La fecha del evento no puede estar en el pasado')
            except (TypeError, ValueError):
                self.add_error('scheduled_date', 'Fecha u hora inválida')

        general_tickets = cleaned_data.get('general_tickets_total')
        vip_tickets = cleaned_data.get('vip_tickets_total')

        if general_tickets is not None:
            if general_tickets < 0:
                self.add_error('general_tickets_total', 'La cantidad de tickets generales no puede ser negativa')
        else:
            general_tickets = 0

        if vip_tickets is not None:
            if vip_tickets < 0:
                self.add_error('vip_tickets_total', 'La cantidad de tickets VIP no puede ser negativa')
        else:
            vip_tickets = 0

        if general_tickets == 0 and vip_tickets == 0:
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
        cleaned_data = super().clean() or {}
        scheduled_date = cleaned_data.get('scheduled_date')
        scheduled_time = cleaned_data.get('scheduled_time')
        
        
        if scheduled_date and scheduled_time:
            try:
               
                naive_datetime = datetime.combine(scheduled_date, scheduled_time)
              
                event_datetime = timezone.make_aware(naive_datetime)
                
              
                print(f"Current time: {timezone.now()}")
                print(f"Event time: {event_datetime}")
                
                if event_datetime < timezone.now():
                    self.add_error('scheduled_date', 'La fecha del evento no puede estar en el pasado')
                    
            except Exception as e:
                self.add_error(None, f"Error al procesar la fecha: {str(e)}")
        
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
        card_number = self.cleaned_data.get('card_number', '')
        if not card_number:
            raise ValidationError('Número de tarjeta requerido')
        
        card_number = card_number.replace(' ', '')
        if not card_number.isdigit() or len(card_number) not in (13, 15, 16):
            raise ValidationError('Número de tarjeta inválido')
        return card_number

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data.get('expiry_date', '')
        if not expiry_date:
            raise ValidationError('La fecha de expiración es requerida')
        
        expiry_date = expiry_date.strip()
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

class RefundRequestForm(forms.ModelForm):
    accept_policy = forms.BooleanField(
        label="Acepto la política de reembolso",
        error_messages={'required': 'Debes aceptar la política para enviar la solicitud.'}
    )

    details = forms.CharField(
        required=False, 
        widget=forms.Textarea(attrs={'placeholder': 'Detalles adicionales (opcional)'}), 
        label='Detalles adicionales'
    )

    class Meta:
        model = RefundRequest
        fields = ['ticket_code', 'reason', 'details', 'accept_policy']
        widgets = {
            'ticket_code': forms.TextInput(attrs={'placeholder': 'Código de ticket'}),
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'ticket_code': 'Código de ticket *',
            'reason': 'Razón del reembolso *',
            'details': 'Detalles adicionales',
        }

    def clean_ticket_code(self):
        ticket_code = self.cleaned_data.get('ticket_code')
        try:
           ticket = Ticket.objects.get(ticket_code=ticket_code)
        except Ticket.DoesNotExist:
            raise forms.ValidationError(
                "El código de ticket no es válido o no está registrado."
            )
        
        existing_request = RefundRequest.objects.filter(ticket_code=ticket_code).exclude(pk=self.instance.pk)
        if existing_request.exists():
            raise forms.ValidationError("Ya existe una solicitud de reembolso para este ticket.")
        
        event = ticket.event
        if event.scheduled_at and (event.scheduled_at - timezone.now()).total_seconds() < 48 * 3600:
            raise forms.ValidationError(
                "No puedes solicitar un reembolso con menos de 48 horas de anticipación al evento."
            )
        return ticket_code

class RefundApprovalForm(forms.ModelForm):
    class Meta:
        model = RefundRequest
        fields = [] 

    approve = forms.BooleanField(required=False, label='Aprobar')
    reject = forms.BooleanField(required=False, label='Rechazar')

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('approve') and cleaned_data.get('reject'):
            raise forms.ValidationError("No puedes aprobar y rechazar al mismo tiempo.")
        if not cleaned_data.get('approve') and not cleaned_data.get('reject'):
            raise forms.ValidationError("Debes seleccionar una acción.")
        return cleaned_data

