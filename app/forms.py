from django import forms
from .models import RefundRequest

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
