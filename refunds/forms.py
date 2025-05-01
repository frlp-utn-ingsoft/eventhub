from django import forms
from .models import Refund

class RefundForm(forms.ModelForm):
    class Meta:
        model = Refund
        fields = ["ticket_code", "reason", "detail"]
        error_messages = {
            "ticket_code": {
                "required": "Indique el código del ticket.",
            },
        }
        widgets = {
            "ticket_code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Escribe el código del ticket aquí...",
            }),
            "detail": forms.Textarea(attrs={
                "class":"form-control",
                "placeholder":"Proporciona más información sobre tu solicitud de reembolso...",
                "rows": 5,
            }),
        }

    reason = forms.ChoiceField(
        label="Motivo del reembolso *",
        choices=[
            ('', 'Selecciona un motivo'),
            ('option1', 'Opción 1'),
            ('option2', 'Opción 2'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        error_messages={'required': 'Indique la razón de la solicitud de reembolso.'}
    )

    accept_policy = forms.BooleanField(
        label="Entiendo y acepto la política de reembolsos.",
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        error_messages={'required': 'Debes aceptar la política de reembolsos para continuar.'}
    )

    def clean_ticket_code(self):
        ticket_code = self.cleaned_data.get("ticket_code")

        if not ticket_code:
            return ticket_code

        if not self.instance.pk:
            if Refund.objects.filter(ticket_code=ticket_code).exists():
                raise forms.ValidationError("Ya existe una solicitud de reembolso para este ticket.")

        return ticket_code
