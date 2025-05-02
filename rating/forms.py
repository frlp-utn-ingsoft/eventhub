from django import forms
from .models import Rating

# Formulario para la reseña
class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ["title", "text", "rating"]
        error_messages = {
            "title": {
                "required": "El título no puede quedar vacío.",
                "max_length": "Máximo 120 caracteres.",
            },
            "text": {
                "required": "Escribe tu reseña antes de publicarla.",
            },
            "rating": {
                "required": "Escribe una calificación entre 1 y 5.",
                "max_value": "La calificación máxima es 5.",
                "min_value": "La calificación mínima es 1.",
            },
        }
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Escribe un título para tu reseña...",
                "maxlength": 120,
            }),
            "text": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Asististe a este evento? Escribe tu opinion acerca de el aqui...",
                "style": "resize:vertical;",
            }),
            "rating": forms.NumberInput(attrs={
                "min": 1,
                "max": 5,
            }),
        }