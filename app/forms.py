from django import forms
from .models import Category
from .models import Notification
from .models import Rating

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

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['title', 'rating', 'text']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Gran experiencia'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Comparte tu experiencia...', 'rows': 3}),
        }
        labels = {
            'title': 'Título de tu reseña *',
            'rating': 'Tu calificación *',
            'text': 'Tu reseña (opcional)',
        }