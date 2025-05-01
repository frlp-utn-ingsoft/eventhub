from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
    class Meta:
        model  = Comment
        fields = ["title", "text"]
        error_messages = {
            "title": {
                "required": "El título no puede quedar vacío.",
                "max_length": "Máximo 120 caracteres.",
            },
            "text": {
                "required": "Escribe tu comentario antes de publicarlo.",
            },
        }
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Escribe un titulo para tu comentario...",
            }),
            "text": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Escribe tu comentario aqui...",
                "style": "resize:vertical;",
            }),
        }
