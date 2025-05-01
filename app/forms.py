from django import forms
from .models import Ticket, Category, Notification

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
