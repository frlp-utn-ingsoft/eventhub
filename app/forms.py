from django import forms
from .models import Category
from .models import Notification

class NotificationForm(forms.ModelForm):
    class Meta:
        model  = Notification
        fields = ["user", "title", "message", "priority"]
        widgets = {"message": forms.Textarea(attrs={"rows":4})}

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
