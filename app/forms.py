from django import forms
from .models import Venue



class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = '__all__'
        labels = {
            'name': 'Nombre del Lugar',
            'address': 'Dirección',
            'city': 'Ciudad',
            'country': 'País',
            'capacity': 'Capacidad',
        }