from django import forms
from django.contrib.auth import get_user_model
from .models import Category
from .models import Notification

User = get_user_model()
class NotificationForm(forms.ModelForm):
    class Meta:
        model  = Notification
        fields = ["user", "priority", "title", "message"]
        widgets = {
            "user":     forms.Select(attrs={
                "class": "form-select select-user",      
                "size": 8                                
            }),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "title":    forms.TextInput(attrs={"class": "form-control"}),
            "message":  forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }
        labels = {
            "user":     "Destinatario",
            "priority": "Prioridad",
            "title":    "Título",
            "message":  "Mensaje",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # solo usuarios NO organizadores
        qs = User.objects.filter(is_organizer=False).order_by("first_name", "last_name")
        self.fields["user"].queryset = qs
        # cómo se muestra cada opción
        self.fields["user"].label_from_instance = (
            lambda u: f"{(u.get_full_name() or u.username).title()} ({u.email})"
        )
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
