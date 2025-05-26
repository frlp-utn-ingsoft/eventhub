
from datetime import datetime
from django import forms
from .models import Event, Notification, RefundRequest, Ticket, User, Venue,Rating,Comment, Category, SurveyResponse
import re
from django.db.models import Sum


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
        elif len(title) > 100:
            self.add_error("title", "El título no debe superar los 100 caracteres.")
        elif len(re.findall(r"[a-zA-Z]", title)) < 10:
            self.add_error("title", "El título debe contener al menos 10 letras.")


        if not message:
            self.add_error("message", "El mensaje no puede estar vacío.")
        elif len(message) < 10:
            self.add_error("message", "El mensaje debe tener al menos 10 caracteres.")
        elif len(message) > 500:
            self.add_error("message", "El mensaje no debe superar los 500 caracteres.")
        elif len(re.findall(r"[a-zA-Z]", message)) < 10:
             self.add_error("message", "El mensaje debe contener al menos 10 letras.")


        if priority not in ["High", "Medium", "Low"]:
            self.add_error("priority", "Prioridad inválida.")

        if tipo_usuario not in ["all", "specific"]:
            self.add_error(None, "Debes seleccionar un destinatario (todos o específico).")
        
        if tipo_usuario == "all":
            if not event:
                self.add_error("event", "Debes seleccionar un evento.")
            else:
                user_ids = (
                    Ticket.objects.filter(event=event)
                    .values_list("user_id", flat=True)
                    .distinct()
                )
                if user_ids.count() < 2:
                    self.add_error("event", "El evento debe tener al menos 2 asistentes para enviar una notificación a todos.")
                    
        if tipo_usuario == "specific" and not user:
            self.add_error("user", "Debes seleccionar un usuario.")
            

class TicketForm(forms.ModelForm):

    # Recibe como parametro el usuario y el evento (los cuales los utilizo en la feature del maximo de 4 entradas por evento)
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
    

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

    quantity = forms.IntegerField(
    label="Cantidad de entradas",
    min_value=1,
    max_value=120,
    widget=forms.TextInput(attrs={'class': 'form-control text-center', 'placeholder': '0'})
    )

    # verifica que el usuario no exeda el maximo de 4 entradas en un mismo evento (ya sea en una sola compra o en varias)
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')

        if quantity is None:
            raise forms.ValidationError("No ha seleccionado la cantidad de tickets a comprar.")

        if quantity > 120:
            raise forms.ValidationError("La cantidad no puede ser mayor a 120.")

        if self.user and self.event:
            total_anteriores = Ticket.objects.filter(
                user=self.user,
                event=self.event
            ).aggregate(total=Sum('quantity'))['total'] or 0

            # Restar el valor original si se está editando un ticket existente
            if self.instance and self.instance.pk:
                total_anteriores -= self.instance.quantity

            if total_anteriores + quantity > 4:
                raise forms.ValidationError("No puede comprar más de 4 entradas para este evento.")

        return quantity

    
    def clean_card_name(self):
        name = self.cleaned_data.get('card_name')
        if not name or name.strip() == "":
            raise forms.ValidationError("El nombre en la tarjeta es obligatorio.")

        if not all(c.isalpha() or c.isspace() for c in name):
            raise forms.ValidationError("El nombre en la tarjeta solo debe contener letras y espacios.")

        return name

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
        
        # --- Validaciones a nivel de campo ---
        
        def clean_capacity(self):
            capacity = self.cleaned_data.get('capacity')
            if capacity is not None: 
                if capacity <= 0:
                    raise forms.ValidationError("La capacidad debe ser un número positivo.")
                if capacity > 100000: 
                    raise forms.ValidationError("La capacidad excede el límite máximo (100,000).")
            return capacity

## agregre el Event_form
class VenueChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: Venue):
        return f"{obj.name} - {obj.city} - {obj.address}"

class EventForm(forms.ModelForm):

    title = forms.CharField(
        label='Título del Evento',
        max_length=60, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    description = forms.CharField(
        label='Descripción',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        max_length=200
    )

    # Definir los campos de la fecha y hora con los widgets correspondientes
    date = forms.DateField( label='Fecha', widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    time = forms.TimeField( label='Hora', widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))

    # Campo de categorías (modelo de relación de varios a varios)
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),  # Establece el queryset directamente aquí
        widget=forms.CheckboxSelectMultiple, 
        required=True,
        label='Categorías'
    )

    venue = VenueChoiceField(  # Use the custom field here
        queryset=Venue.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label='Ubicación',
        empty_label="Selecciona una ubicación",  # Opcional
        to_field_name="id",  # Opcional
    )

    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'time', 'categories', 'venue']  # Añadí 'date' y 'time' al form
        labels = {
            'title': 'Título del Evento',
            'description': 'Descripción',
            'date': 'Fecha',
            'time': 'Hora',
            'categories': 'Categorías',
            'venue': 'Ubicación',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Asignación de clases a los campos para estilizar
        self.fields['title'].widget.attrs.update({'class': 'form-control'})
        self.fields['description'].widget.attrs.update({'class': 'form-control', 'rows': 4})
        self.fields['venue'].widget.attrs.update({'class': 'form-control'})
        self.fields['date'].widget.attrs.update({'class': 'form-control'})
        self.fields['time'].widget.attrs.update({'class': 'form-control'})
        

    # Agregar validaciones personalizadas
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title:
            raise forms.ValidationError("El título es obligatorio.")
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description:
            raise forms.ValidationError("La descripción es obligatoria.")
        return description

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if not date:
            raise forms.ValidationError("La fecha es obligatoria.")
        if date:
            today = date.today()
            if date < today:
                raise forms.ValidationError("La fecha del evento debe ser hoy o posterior.")
        return date

    def clean_time(self):
        time = self.cleaned_data.get('time')
        if not time:
            raise forms.ValidationError("La hora es obligatoria.")
        return time

    def clean_categories(self):
        categories = self.cleaned_data.get('categories')
        # Si deseas que al menos una categoría esté seleccionada:
        if not categories:
            raise forms.ValidationError("Debes seleccionar al menos una categoría.")
        return categories

    def clean_venue(self):
        venue = self.cleaned_data.get('venue')
        if not venue:
            raise forms.ValidationError("La ubicación es obligatoria.")
        return venue

class SurveyForm(forms.ModelForm):
    class Meta:
        model = SurveyResponse
        fields = ['satisfaction', 'issue', 'recommend']
        widgets = {
            'issue': forms.Textarea(attrs={'rows': 3}),
            'recommend': forms.RadioSelect(choices=[(True, 'Sí'), (False, 'No')]),
        }