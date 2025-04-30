from django import forms
from .models import RefundRequest
from .models import Ticket

class RefundRequestForm(forms.ModelForm):
    class Meta:
        model = RefundRequest
        fields = ["ticket_code", "reason"]

        #valido el campo reason antes de guardar el formulario
        def clean_reason(self):
            #Obtengo el valor del campo reason y si no es valido o tiene < 10 caract, tira error
            reason = self.cleaned_data.get("reason")
            if not reason or len(reason.strip()) < 10:
                raise forms.ValidationError("El motivo debe tener al menos 10 caracteres.")
            # Si el motivo es valido, lo devuelvo
            return reason
        
        #valido el campo ticket antes de guardar el formulario, misma logica que el anterior
        def clean_ticket_code(self):
            ticket_code = self.cleaned_data.get("ticket_code")

        #intentamos encontrar un ticket con ese código
            try:
                Ticket.objects.get(ticket_code=ticket_code)
            except Ticket.DoesNotExist:
                raise forms.ValidationError("El ticket no existe.")

        #verifico si ya hay una solicitud para ese ticket
            if RefundRequest.objects.filter(ticket_code=ticket_code).exists():
                raise forms.ValidationError("Ya existe una solicitud de reembolso para este ticket.")

        #devolvemos el código
            return ticket_code
