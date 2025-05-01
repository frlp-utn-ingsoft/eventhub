from django import forms
from .models import Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model  = Category
        fields = ("name", "description", "is_active")
        widgets = {
            "name":        forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "is_active":   forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        error_messages = {
            "name": {
                "required": "El nombre de la categoría es necesario.",
                "max_length": "Máximo 60 caracteres.",
            },
        }

