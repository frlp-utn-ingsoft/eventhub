from django import forms
from .models import RefundRequest, Event
from django.core.exceptions import ValidationError

class RefundRequestForm(forms.ModelForm):
    MOTIVO_CHOICES = [
        ('vuelo_cancelado', 'Vuelo cancelado'),
        ('equipaje_perdido', 'Equipaje perdido'),
        ('cambio_itinerario', 'Cambio de itinerario'),
        ('otro', 'Otro'),
    ]

    motivo = forms.ChoiceField(
        choices=MOTIVO_CHOICES,
        label="Motivo de reembolso",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    detalles = forms.CharField(
        label="Detalles adicionales",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "class": "form-control"})
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

        # Si estamos editando (hay instancia con reason)
        if self.instance and self.instance.pk:
            reason = self.instance.reason or ""

            # Separamos en motivo y detalles (si hay ": ")
            motivo_text = reason
            detalles_text = ""
            if ": " in reason:
                motivo_text, detalles_text = reason.split(": ", 1)

            # Ahora buscamos la clave en MOTIVO_CHOICES que tenga ese motivo
            motivo_key = None
            for key, val in self.MOTIVO_CHOICES:
                if val == motivo_text:
                    motivo_key = key
                    break

            # Si encontramos, asignamos los valores iniciales
            if motivo_key:
                self.initial['motivo'] = motivo_key
            else:
                self.initial['motivo'] = 'otro'  # fallback

            self.initial['detalles'] = detalles_text

    def clean_ticket_code(self):
        code = self.cleaned_data['ticket_code'].strip()
        if not code:
            raise ValidationError("El código de ticket es obligatorio.")
        # Debe existir un Event con ese ID
        try:
            event_id = int(code)
            Event.objects.get(pk=event_id)
        except (ValueError, Event.DoesNotExist):
            raise ValidationError("Código de ticket inválido: no existe ese evento.")
        return code

    def clean_detalles(self):
        text = self.cleaned_data.get('detalles', '').strip()
        if len(text) > 500:
            raise ValidationError("Detalles demasiado largos (máx. 500 caracteres).")
        return text

    def clean(self):
        cleaned = super().clean()
        code = cleaned.get('ticket_code')

        # Validación de duplicados solo en creación (instance.pk es None)
        if code and self.user and self.instance.pk is None:
            hay = RefundRequest.objects.filter(
                user=self.user,
                ticket_code=code,
                approved__isnull=True
            ).exists()
            if hay:
                raise ValidationError("Ya tenés una solicitud pendiente para ese ticket.")

        return cleaned

    def save(self, commit=True):
        motivo = dict(self.MOTIVO_CHOICES)[self.cleaned_data['motivo']]
        detalles = self.cleaned_data.get('detalles', '').strip()
        razon = motivo
        if detalles:
            razon += f": {detalles}"
        instance = super().save(commit=False)
        instance.reason = razon
        if commit:
            instance.save()
        return instance
