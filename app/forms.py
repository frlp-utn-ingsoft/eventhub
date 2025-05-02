from django import forms
from .models import Venue

class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = ['name', 'address', 'city', 'capacity', 'contact']

from .models import RefundRequest, Ticket, Category, Notification, Event, Rating
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model


User = get_user_model()
# --- Formulario de Refunds ---
class RefundRequestForm(forms.ModelForm):
    MOTIVO_CHOICES = [
        ('', 'Seleccione un motivo…'),
        ('enfermedad', 'Enfermedad comprobable'),
        ('fuerza_mayor', 'Fuerza mayor (accidente, urgencia familiar)'),
        ('clima_extremo', 'Clima extremo o fenómenos naturales'),
        ('covid', 'Restricciones o contagio de COVID-19'),
        ('problema_transporte', 'Problema de transporte terrestre'),
        ('agenda_conflicto', 'Conflicto de agenda o cambio de planes'),
        ('otro', 'Otro'),
    ]

    motivo = forms.ChoiceField(
        choices=MOTIVO_CHOICES,
        label="Motivo de reembolso",
        widget=forms.Select(attrs={"class": "form-select"}),
        error_messages={'required': 'Debes seleccionar un motivo.'}
    )
    detalles = forms.CharField(
        label="Detalles adicionales",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "class": "form-control"})
    )
    acepta_politicas = forms.BooleanField(
        label="He leído y acepto las políticas de reembolso",
        required=True,
        error_messages={'required': 'Debes aceptar las políticas para continuar.'},
    )

    class Meta:
        model = RefundRequest
        fields = ["ticket_code"]
        widgets = {
            "ticket_code": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Precarga motivo y detalles al editar
        if self.instance and self.instance.pk:
            self.fields.pop('acepta_politicas')
            reason = self.instance.reason or ""
            motivo_text, detalles_text = (reason.split(": ", 1) + [""])[:2]
            # asignar initial
            key = next((k for k,v in self.MOTIVO_CHOICES if v == motivo_text), 'otro')
            self.initial.update({'motivo': key, 'detalles': detalles_text})

    def clean_ticket_code(self):
        code = self.cleaned_data['ticket_code'].strip()
        if not code:
            raise ValidationError("El código de ticket es obligatorio.")

        # 1) Buscamos el Ticket
        try:
            ticket = Ticket.objects.get(ticket_code=code)
        except Ticket.DoesNotExist:
            raise ValidationError("Código de ticket inválido: no existe ese Ticket.")

        # 2) Tomamos la fecha del evento desde scheduled_at
        event_dt = ticket.event.scheduled_at   # DateTimeField
        event_date = event_dt.date()           # convertimos a date

        # 3) Calculamos días pasados hasta hoy
        today = timezone.localdate()           # equivalente a timezone.now().date()
        dias_pasados = (today - event_date).days

        if dias_pasados > 30:
            raise ValidationError(
                f"Han pasado {dias_pasados} días desde el evento ({event_date}); "
                "ya no se aceptan reembolsos."
            )

        # Lo guardamos por si lo necesitás en save()
        self.cleaned_data['ticket_obj'] = ticket
        return code


    def clean_detalles(self):
        text = self.cleaned_data.get('detalles', '').strip()
        if len(text) > 500:
            raise ValidationError("Detalles demasiado largos (máx. 500 caracteres).")
        return text

    def clean(self):
        cleaned = super().clean()
        ticket_code = cleaned.get('ticket_code')

        # Validación de duplicados de solicitudes pendientes
        if ticket_code and self.user and self.instance.pk is None:
            if RefundRequest.objects.filter(
                user=self.user,
                ticket_code=ticket_code,
                approved__isnull=True
            ).exists():
                raise ValidationError("Ya tenés una solicitud pendiente para ese ticket.")
        return cleaned

    def save(self, commit=True):
        motivo_label = dict(self.MOTIVO_CHOICES).get(self.cleaned_data['motivo'], '')
        detalles = self.cleaned_data.get('detalles', '').strip()
        razon = motivo_label + (f": {detalles}" if detalles else "")

        instance = super().save(commit=False)
        instance.reason = razon

        if commit:
            instance.save()
        return instance

# --- Formulario de Tickets ---
class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['quantity', 'type'] 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['quantity'].widget.attrs.update({
            'class': 'form-control text-center',
            'min': '1',
            'id': 'id_quantity',
            'inputmode': 'numeric'
        })

        self.fields['quantity'].initial = 1
        self.fields['type'].initial = 'GENERAL'
        self.fields['type'].widget.attrs.update({
            'class': 'form-select'
        })

# --- Formulario de Notificaciones ---
class NotificationForm(forms.ModelForm):
    TARGET_CHOICES = [
        ('event', 'Todos los asistentes de un evento'),
        ('user', 'Un usuario específico')
    ]
    # Campo auxiliar para el tipo de destinatario (radio buttons)
    target = forms.ChoiceField(choices=TARGET_CHOICES, widget=forms.RadioSelect, label='Destino')
    # Campos de destino condicionales
    event = forms.ModelChoiceField(queryset=Event.objects.none(), required=False, label='Evento')
    user = forms.ModelChoiceField(queryset=User.objects.none(), required=False, label='Usuario')
    
    class Meta:
        model = Notification
        fields = ['target', 'event', 'user', 'title', 'message', 'priority', 'to_all_event_attendees']
        widgets = {
            'to_all_event_attendees': forms.HiddenInput()  # ocultamos el checkbox real
        }
        labels = {
            'title': 'Título',
            'message': 'Mensaje',
            'priority': 'Prioridad',
        }
    
    def __init__(self, *args, **kwargs):
        # Recibimos el usuario actual para filtrar opciones
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Ajustar el queryset de eventos y usuarios según el usuario logueado
        if user:
            # Mostrar solo eventos organizados por el usuario (asumiendo Event.organizer relaciona al organizador)
            self.fields['event'].queryset = Event.objects.filter(organizer=user)
            # Mostrar solo usuarios que tengan tickets en eventos del organizador (asistentes de cualquiera de sus eventos)
            self.fields['user'].queryset = User.objects.filter(tickets__event__organizer=user).distinct()
        # Inicializar selección por defecto: ninguno (se fuerza al usuario a elegir)
        self.fields['target'].initial = None
        # Ocultar el campo booleano en el formulario (lo controlaremos manualmente)
        self.fields['to_all_event_attendees'].initial = False

    def clean(self):
        cleaned_data = super().clean()
        target_choice = cleaned_data.get('target')
        event = cleaned_data.get('event')
        user = cleaned_data.get('user')
        # Validar según la opción de destino elegida
        if target_choice == 'event':
            # Debe haber un evento y marcar checkbox de "todos asistentes"
            if not event:
                raise forms.ValidationError("Por favor, seleccioná un evento para enviar la notificación.")
            # Forzamos to_all_event_attendees a True porque el usuario eligió evento
            cleaned_data['to_all_event_attendees'] = True
            cleaned_data['user'] = None  # Asegurarse de no usar campo de usuario
        elif target_choice == 'user':
            # Debe haber un usuario
            if not user:
                raise forms.ValidationError("Por favor, seleccioná un usuario específico para enviar la notificación.")
            cleaned_data['to_all_event_attendees'] = False
            cleaned_data['event'] = None  # No debe usarse el evento en este caso
        else:
            # Si no se eligió ninguna opción (no debería ocurrir si el campo es requerido)
            raise forms.ValidationError("Debés elegir un tipo de destino (evento o usuario).")
        return cleaned_data
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Nombre',
            'description': 'Descripción',
            'is_active': 'Activo',
        }

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['title', 'rating', 'text']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Gran experiencia'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Comparte tu experiencia...', 'rows': 3}),
        }
        labels = {
            'title': 'Título de tu reseña *',
            'rating': 'Tu calificación *',
            'text': 'Tu reseña (opcional)',
        }
