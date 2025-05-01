from django import forms
from .models import Rating
from .models import Category

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

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'is_active']
        labels = {
            'name': 'Nombre',
            'description': 'Descripción',
            'is_active': 'Activo',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        error_messages = {
            'name': {
                'required': 'Por favor, ingrese un nombre',
            },
            'description': {
                'required': 'Por favor, ingrese una descripción',
            },
        }

    def clean_name(self):
        name = self.cleaned_data.get("name")

        if not name:
            raise forms.ValidationError("El nombre es obligatorio")

        if len(name) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 caracteres")

        if len(name) > 100:
            raise forms.ValidationError("El nombre no puede tener más de 100 caracteres")

        qs = Category.objects.filter(name=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("Ya existe una categoría con ese nombre")

        return name

    def clean_description(self):
        description = self.cleaned_data.get("description")

        if not description:
            raise forms.ValidationError("La descripción es obligatoria")

        if len(description) < 10:
            raise forms.ValidationError("La descripción debe tener al menos 10 caracteres")

        if len(description) > 500:
            raise forms.ValidationError("La descripción no puede tener más de 500 caracteres")

        return description

