from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
    class Meta:
        model  = Comment
        fields = ["title", "text"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Escribe nu titulo para tu comentario...",
            }),
            "text": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Escribe tu comentario aqui...",
                "style": "resize:vertical;",
            }),
        }
