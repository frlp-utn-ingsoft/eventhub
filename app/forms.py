from django import forms

from .models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['title', 'content']  # Incluye 'title'
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Escribe un título para tu comentario...'}),
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Escribe tu comentario aquí...'}),
        }