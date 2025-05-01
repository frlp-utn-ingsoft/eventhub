from django import forms
from .models import Rating, Venue, Event
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import re


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



class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = ['name', 'address', 'city', 'capacity', 'contact']
        labels = {
            'name': 'Nombre de la ubicación',
            'address': 'Dirección',
            'city': 'Ciudad',
            'capacity': 'Capacidad (número de personas)',
            'contact': 'Contacto',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Ej: Estadio Nacional',
                'class': 'form-control',
                'maxlength': '100'
            }),
            'address': forms.TextInput(attrs={
                'placeholder': 'Ej: Av. Grecia 2001',
                'class': 'form-control'
            }),
            'city': forms.TextInput(attrs={
                'placeholder': 'Chile',
                'class': 'form-control',
                'maxlength': '100'
            }),
            'capacity': forms.NumberInput(attrs={
                'placeholder': 'Ej: 1000',
                'class': 'form-control'
            }),
            'contact': forms.Textarea(attrs={
                'placeholder': 'Ej: contacto@email.com o +54 911 12345678',
                'class': 'form-control',
                'rows': 3,
                'maxlength': '100'
            }),
        }

    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')
        if capacity is not None and capacity <= 0:
            raise ValidationError("La capacidad no puede ser cero.")
        return capacity

    def clean_contact(self):
        contact = self.cleaned_data.get('contact', '').strip()

        email_valid = True
        try:
            validate_email(contact)
        except ValidationError:
            email_valid = False

        phone_valid = bool(re.match(r'^\+?\d[\d\s\-\(\)]{7,}$', contact))

        if not (email_valid or phone_valid):
            raise ValidationError("El contacto debe ser un número de teléfono válido o una dirección de email.")
        
        return contact


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'scheduled_at', 'venue']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'scheduled_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'venue': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        venues = Venue.objects.all()
        if venues.exists():
            self.fields['venue'].queryset = venues
        else:
            self.fields['venue'].choices = [('', 'No hay ubicaciones disponibles')]
            self.fields['venue'].disabled = True
