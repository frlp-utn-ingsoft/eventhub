from django import forms
from .models import Refund

class RefundForm(forms.ModelForm):
    class Meta:
        model = Refund
        fields = ["ticket_code", "reason"]
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