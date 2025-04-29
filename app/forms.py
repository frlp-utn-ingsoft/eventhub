from django import forms
from .models import Rating

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['title', 'score', 'comment']

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise forms.ValidationError("El título no puede estar vacío.")
        return title

    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '').strip()
        if not comment:
            raise forms.ValidationError("El comentario no puede estar vacío.")
        return comment

    def clean_score(self):
        score = self.cleaned_data.get('score')
        if not score:
            raise forms.ValidationError("Debe seleccionar una calificación.")
        return score
