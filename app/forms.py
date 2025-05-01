from django import forms
from .models import RefundRequest, Ticket, Event
from django.core.exceptions import ValidationError
from django.utils import timezone

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

    # clean_ticket_code
    def clean_ticket_code(self):
        ticket_code = self.cleaned_data['ticket_code'].strip()
        if not ticket_code:
            raise ValidationError("El código de ticket es obligatorio.")

        # 1) Buscamos el Ticket
        try:
            ticket = Ticket.objects.get(ticket_code=ticket_code)
        except Ticket.DoesNotExist:
            raise ValidationError("Código de ticket inválido: no existe ese Ticket.")

        # 2) Tomamos la fecha del evento (DateField o DateTimeField)
        event_date = ticket.event.date  

        # 3) Calculamos cuántos días pasaron
        dias = (timezone.now().date() - event_date).days

        if dias > 30:
            # Mensaje bien formateado
            raise ValidationError(
                f"Han pasado {dias} días desde el evento ({event_date}); "
                "ya no se aceptan reembolsos."
            )

        # guardamos el ticket por si lo necesitás en save()
        self.cleaned_data['ticket_obj'] = ticket
        return ticket_code


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