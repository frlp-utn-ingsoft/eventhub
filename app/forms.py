from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Category, Comment, Event, RefundRequest, Venue


class EventForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    class Meta:
        model = Event
        fields = ['title', 'description', 'scheduled_at', 'venue', 'categories', 'premium' , 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'scheduled_at': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control'
                },
                format='%Y-%m-%dT%H:%M'
            ),
            'categories': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'venue': forms.Select(attrs={'class': 'form-select'})
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['scheduled_at'].input_formats = ['%Y-%m-%dT%H:%M'] # type: ignore
        if self.user:
            self.fields['venue'].queryset = Venue.objects.filter(created_by=self.user) # type: ignore

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title.strip()) < 5: # type: ignore
            raise ValidationError("El título debe tener al menos 5 caracteres.")
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description.strip()) < 20: # type: ignore
            raise ValidationError("La descripción debe tener al menos 20 caracteres.")
        return description

    def clean_scheduled_at(self):
        scheduled_at = self.cleaned_data.get('scheduled_at')
        if scheduled_at and scheduled_at < timezone.now():
            raise ValidationError("La fecha/hora debe ser futura.")
        return scheduled_at
    
    def save(self, commit=True):
        event = super().save(commit=False)
        event.organizer = self.user
        if commit:
            event.save()
            self.save_m2m() 
        if event.venue:
            event.available_tickets = event.venue.capacity
            event.save()

        return event
    
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("El nombre es obligatorio.")
        # Puedes agregar más validaciones si es necesario
        return name


class CommentForm (forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Titulo del comentario...'}),
            'content': forms.Textarea(attrs={'placeholder': 'Escribe tu comentario...'}),
        }

class RefundRequestForm(forms.ModelForm):
    accept_policy = forms.BooleanField(
        label="Acepto la política de reembolsos",
        required=True
    )

    class Meta:
        model = RefundRequest
        fields = ['reason', 'policy_30_days']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Proporciona más información...'})
        }
