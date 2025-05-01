from django import forms
from .models import Category
from .models import Notification

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
