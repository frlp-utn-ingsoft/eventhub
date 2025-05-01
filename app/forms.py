from django import forms
from .models import RefundRequest, Ticket
from django.utils import timezone

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