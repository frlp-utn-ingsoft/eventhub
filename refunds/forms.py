from django import forms
from .models import Refund

class RefundForm(forms.ModelForm):
    class Meta:
        model = Refund
        fields = ["ticket_code","reason"]
        error_messages = {
            "ticket_code": {
                "required": "Indique el código del ticket.",
            },
            "reason": {
                "required": "Indique la razón de la solicitud de reembolso.",
            },
        }
        widgets = {
            "ticket_code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Escribe el código del ticket aquí...",
            }),
            "text": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Escribe el motivo de tu solicitud aquí...",
                "style": "resize:vertical;",
            }),
        }
     