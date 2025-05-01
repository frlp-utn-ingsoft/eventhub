from django import forms
from .models import RefundRequest, Ticket, Category, Notification, Event
from django.core.exceptions import ValidationError
from django.utils import timezone

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
    class Meta:
        model  = Notification
        fields = ["user", "priority", "title", "message"]
        widgets = {
            "user":     forms.Select(attrs={"class": "form-select"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "title":    forms.TextInput(attrs={"class": "form-control"}),
            "message":  forms.Textarea(attrs={
                            "class": "form-control",
                            "rows": 4
                        }),
        }
        labels = {
            "user":     "Destinatario",
            "priority": "Prioridad",
            "title":    "Título",
            "message":  "Mensaje",
        }

# --- Formulario de Categorías ---
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

