from django import forms
from .models import RefoundRequest, Ticket
from django.utils import timezone

class RefoundRequestForm(forms.ModelForm):
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
        model = RefoundRequest
        # Solo incluimos ticket_code, reason, details y accept_policy
        fields = ['ticket_code', 'reason', 'details', 'accept_policy']
        widgets = {
            'ticket_code': forms.TextInput(attrs={'placeholder': 'Código de ticket'}),
        }
        labels = {
            'ticket_code': 'Código de ticket *',
            'details': 'Detalles adicionales',
        }

    def clean_ticket_code(self):
        ticket_code = self.cleaned_data.get('ticket_code')
        
        # 1) Validar que el ticket exista
        try:
            ticket = Ticket.objects.get(ticket_code=ticket_code)
        except Ticket.DoesNotExist:
            raise forms.ValidationError(
                "El código de ticket no es válido o no está registrado."
            )

        # 2) Comprobar que el evento asociado tenga +48 h de anticipación
        event = ticket.event
        if event.scheduled_at and (event.scheduled_at - timezone.now()).total_seconds() < 48 * 3600:
            raise forms.ValidationError(
                "No puedes solicitar un reembolso con menos de 48 horas de anticipación al evento."
            )

        # No guardamos ni exponemos el `event` en el modelo, solo validamos
        return ticket_code
