
from datetime import datetime
from django import forms
from .models import Event, Notification, RefundRequest, Ticket, User, Venue,Rating,Comment


class NotificationForm(forms.ModelForm):
    event = forms.ModelChoiceField(
        queryset=Event.objects.all(),
        required=False,
        label="Evento relacionado",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label="Usuario específico",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = Notification
        fields = ["title", "message", "priority","event"]  

        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: Cambio de horario del evento"
            }),
            "message": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Escribe tu mensaje aquí"
            }),
            "priority": forms.Select(attrs={
                "class": "form-select"
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get("title")
        message = cleaned_data.get("message")
        priority = cleaned_data.get("priority")
        event = cleaned_data.get("event")
        user = cleaned_data.get("user")
        tipo_usuario = self.data.get("tipo_usuario")

        if not title:
            self.add_error("title", "El título no puede estar vacío.")
        elif len(title) < 10:
            self.add_error("title", "El título debe tener al menos 10 caracteres.")
        elif Notification.objects.filter(title=title).exclude(pk=self.instance.pk).exists():
            self.add_error("title", "Ese título ya existe.")

        if not message:
            self.add_error("message", "El mensaje no puede estar vacío.")
        elif len(message) < 10:
            self.add_error("message", "El mensaje debe tener al menos 10 caracteres.")

        if priority not in ["High", "Medium", "Low"]:
            self.add_error("priority", "Prioridad inválida.")

        if tipo_usuario == "all" and not event:
            self.add_error("event", "Debes seleccionar un evento.")
        if tipo_usuario == "specific" and not user:
            self.add_error("user", "Debes seleccionar un usuario.")

class TicketForm(forms.ModelForm):
    # Campos de la tarjeta, validaciones específicas en los métodos clean_* correspondientes
    card_name = forms.CharField(label="Nombre en la tarjeta", max_length=30, widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'Juan Peres'}))
    card_number = forms.CharField(label="Número de tarjeta", max_length=25, min_length=13, widget=forms.TextInput(attrs={'class': 'form-control','placeholder': '1234 5678 9012 3456'}))
    expiration_date = forms.CharField(label="Fecha de expiración (MM/AA)", max_length=5, widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'MM/AA'}))
    cvv = forms.CharField(label="CVV", max_length=4, widget=forms.TextInput(attrs={'class': 'form-control','placeholder': '123'}))

    # Tipo de entrada con dos opciones posibles (General y VIP)
    ENTRY_TYPE_CHOICES = [
        ("GENERAL", "GENERAL"),
        ("VIP", "VIP"),
    ]
    type = forms.ChoiceField(label="Tipo de Entrada", choices=ENTRY_TYPE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Ticket
        fields = ['quantity', 'type']  # Solo estos campos se cargan en el formulario

    accept_terms = forms.BooleanField(
    required=True,
    label="Acepto los términos y condiciones de privacidad",
    widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')

        # Verificar si quantity es None o 0
        if quantity is None:
            raise forms.ValidationError("No ha seleccionado la cantidad de tickets a comprar")

        # Validar que la cantidad no sea mayor a 120
        if quantity > 120:
            raise forms.ValidationError("La cantidad no puede ser mayor a 120.")

        return quantity

    def clean_card_number(self):
        number = self.cleaned_data.get('card_number')

        # Verificación de que no esté vacío
        if not number or number.strip() == "":
            raise forms.ValidationError("El número de la tarjeta es obligatorio")

        # Eliminar espacios en blanco
        number = number.replace(" ", "")

        # Validar si el número es solo dígitos
        if not number.isdigit():
            raise forms.ValidationError("El número de la tarjeta debe contener solo números")

        # Validar longitud: 13 o 16
        if len(number) not in [13, 16]:
            raise forms.ValidationError("El número de la tarjeta debe tener 13 o 16 dígitos")

        return number

    def clean_cvv(self):
        cvv = self.cleaned_data.get('cvv')

        # Verificar si el CVV está vacío
        if not cvv or cvv.strip() == "":
            raise forms.ValidationError("El CVV es obligatorio.")

        # Validar si es un número y que tenga 3 o 4 dígitos
        if not cvv.isdigit() or not (3 <= len(cvv) <= 4):
            raise forms.ValidationError("El CVV debe tener 3 o 4 dígitos.")

        return cvv

    def clean_expiration_date(self):
        expiration_date = self.cleaned_data.get('expiration_date')

        # Verificar que la fecha de expiración tiene el formato correcto (MM/AA)
        if not expiration_date or len(expiration_date) != 5 or expiration_date[2] != '/':
            raise forms.ValidationError("El formato de la fecha de expiración debe ser MM/AA.")
        
        # Verificar si el mes y año son válidos (esto es opcional, pero sería una buena validación adicional)
        try:
            month, year = map(int, expiration_date.split('/'))
            if not (1 <= month <= 12):
                raise forms.ValidationError("El mes debe ser un valor entre 01 y 12.")
            
            # Verificar si la tarjeta está caducada
            current_year = datetime.now().year % 100  # Año actual en formato AA
            current_month = datetime.now().month
            if year < current_year or (year == current_year and month < current_month):
                raise forms.ValidationError("La tarjeta está caducada.")

        except ValueError:
            raise forms.ValidationError("La fecha de expiración no es válida.")

        return expiration_date
    
class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['title', 'text', 'rating']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título de la reseña'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Escribí tu opinión...'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
        }
        labels = {
            'title': 'Título',
            'text': 'Comentario',
            'rating': 'Puntaje (1-5)',
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')

        if rating is None:
            raise forms.ValidationError("Debes ingresar un puntaje.")
        if not (1 <= rating <= 5):
            raise forms.ValidationError("El puntaje debe estar entre 1 y 5.")
        return rating
    

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['tittle', 'text']
        widgets = {
            'tittle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingresa el título de tu comentario'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Escribe el contenido del comentario aquí', 'rows': 4}),
        }
class RefundRequestForm(forms.ModelForm):
    class Meta:
        model = RefundRequest
        fields = ['ticket_code', 'reason']
        widgets = {
            'ticket_code': forms.TextInput(attrs={'class': 'form-control'}),
             'reason': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Explicá el motivo'}),
        }   


class VenueForm(forms.ModelForm):
        name = forms.CharField(label='Nombre de la ubicación', max_length=30, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Estadio Nacional'}))
        address = forms.CharField(label='Dirección', max_length=40, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Av. Grecia 2001'}))
        city = forms.CharField(label='Ciudad', max_length=40, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Buenos Aires'}))
        capacity = forms.IntegerField(label='Capacidad (Número de Personas)', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 1000'}))
        contact = forms.CharField(label='Contacto', widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe las características principales de la ubicación...', 'rows': 5}))

        class Meta:
            model = Venue
            fields = ['name', 'address', 'city', 'capacity', 'contact']
            # Ya no necesitamos definir widgets aquí porque los definimos arriba
