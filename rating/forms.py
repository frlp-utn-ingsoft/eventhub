from django import forms
from .models import Rating

# Formulario para la reseña
class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['title', 'text', 'rating']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Titulo'}),
            'text': forms.Textarea(attrs={'placeholder': 'Reseña'}),
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
        }