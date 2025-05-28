
import datetime
from django import forms
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django import forms
from django.utils import timezone
from django_countries.fields import CountryField
from cities_light.models import City
from decimal import Decimal
import random, string
from django.core.exceptions import ValidationError


def save(method):
    def wrapper(self, *args, **kwargs):
        result = method(self, *args, **kwargs)
        self.save()
        return result
    return wrapper

class User(AbstractUser):
    is_organizer = models.BooleanField(default=False)

    @classmethod
    def validate_new_user(cls, email, username, password, password_confirm):
        errors = {}

        if email is None:
            errors["email"] = "El email es requerido"
        elif User.objects.filter(email=email).exists():
            errors["email"] = "Ya existe un usuario con este email"

        if username is None:
            errors["username"] = "El username es requerido"
        elif User.objects.filter(username=username).exists():
            errors["username"] = "Ya existe un usuario con este nombre de usuario"

        if password is None or password_confirm is None:
            errors["password"] = "Las contraseñas son requeridas"
        elif password != password_confirm:
            errors["password"] = "Las contraseñas no coinciden"

        return errors
    
class Venue(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField("Nombre del Lugar", max_length=255)
    address = models.CharField("Dirección", max_length=255)
    capacity = models.IntegerField("Capacidad")
    country = CountryField("País")
    city = models.CharField("Ciudad", max_length=255)
    created_at = models.DateTimeField("Fecha de Creación", auto_now_add=True)
    updated_at = models.DateTimeField("Fecha de Actualización", auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.city}, {self.country}"

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
    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')
        if capacity is None:
            raise forms.ValidationError("Este campo es obligatorio.")
        if capacity < 1:
            raise forms.ValidationError("La capacidad debe ser un número entero positivo.")
        return capacity
    
class Category(models.Model):
    name = models.CharField(max_length=40)
    description = models.TextField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    @classmethod
    def new(cls, name, description):    
        category = Category.objects.create(
            name=name,
            description=description
        )
        return category
    
    def update(self, name, description):
        self.name = name or self.name
        self.description = description or self.description
        self.updated_at = timezone.now()
        self.save()


class Event(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    categories = models.ManyToManyField(Category, related_name='events')
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='events')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    @property
    def tickets_sold(self):
        return sum(ticket.quantity for ticket in self.tickets.all()) # type: ignore
    
    @property
    def demand_message(self):
        if not self.venue or self.venue.capacity == 0:
            return "Capacidad indefinida"
        
        percent = (self.tickets_sold/self.venue.capacity)*100

        if percent > 90:
            return "ALTA"
        elif percent < 10:
            return "BAJA"
        else:
            return "MEDIA"


    def __str__(self):
        return self.title

    @classmethod
    def validate(cls, title, description, scheduled_at):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"

        if description == "":
            errors["description"] = "Por favor ingrese una descripcion"

        return errors

    @classmethod
    def new(cls, title, description, scheduled_at, organizer, categories=None, venue=None, price=0.00):
        # Validaciones y creación
        errors = cls.validate(title, description, scheduled_at)
        if not organizer:
            errors["organizer"] = "El organizador es obligatorio"
        if not venue:
            errors["venue"] = "La sede es obligatoria"
        if errors:
            return False, errors

        event = cls.objects.create(
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            organizer=organizer,
            venue=venue,
            price=price
        )
        if categories:
            event.categories.set(categories)
        return True, event
    
    @property
    def rating_average(self):
        rating = self.ratings.all() # type: ignore
        if rating.exists():
            return round(sum(r.calificacion for r in rating) / rating.count(), 2)
        return 0


    def update(self, title, description, scheduled_at, organizer):
        self.title = title or self.title
        self.description = description or self.description
        self.scheduled_at = scheduled_at or self.scheduled_at
        self.organizer = organizer or self.organizer

        self.save()

class Coupon(models.Model):
    id = models.AutoField(primary_key=True)
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='coupons')
    code = models.CharField(max_length=10, unique=True, editable=False)
    discount_percent = models.PositiveSmallIntegerField()
    active = models.BooleanField(default=True)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_unique_code()
        super().save(*args, **kwargs)

    def generate_unique_code(self, length=8):
        characters = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choices(characters, k=length))
            if not Coupon.objects.filter(code=code).exists():
                return code

    def __str__(self):
        return f'{self.code} - {self.discount_percent}% - Evento: {self.event.title}'
    
    def clean(self):
        if self.expiration_date < timezone.now():
            raise ValidationError("La fecha de expiración no puede ser en el pasado.")
    
#comentarios
class Comment(models.Model):
    title = models.CharField(max_length=200)
    text = models.CharField(max_length=140)
    created_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="comments")

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    @classmethod
    def validate(cls, title, text):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"
        if len(title)>200:
            errors["title"] = "El título no debe exceder los 200 caracteres" 
        if not title.strip():
            errors["title"] = "Por favor ingrese un título válido"      

        if text == "":
            errors["text"] = "Por favor ingrese un mensaje"
        if len(text)>140:
            errors["text"] = "El comentario no debe exceder los 140 caracteres"  
        if not text.strip():
            errors["text"] = "Por favor ingrese un comentario válido"     

        return errors

    @classmethod
    def new(cls, title, text, user, event):
        errors = Comment.validate(title, text)

        if len(errors.keys()) > 0:
            return False, errors

        Comment.objects.create(
            title=title,
            text=text,
            user=user,
            event=event
        )

        return True, None

    def update(self, title, text):
        errors = Comment.validate(title, text)

        if len(errors.keys()) > 0:
            return False, errors
        
        self.title = title or self.title
        self.text = text or self.text
        self.save()

        return True, None
    
class Ticket(models.Model):
    TICKET_TYPES= [('general', 'General'), ('vip', 'VIP')]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tickets")
    buy_date = models.DateTimeField(auto_now_add=True)
    ticket_code = models.CharField(max_length=100, unique=True, editable=False)
    quantity = models.PositiveIntegerField(default=1)
    type = models.CharField(max_length=10, choices=TICKET_TYPES, default='general')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def save(self, *args, **kwargs):
        if not self.ticket_code:
            self.ticket_code = str(uuid.uuid4())
        super().save(*args, **kwargs)  

    def __str__(self):
        return f"{self.user.username} - {self.event.title} - {self.ticket_code}"
    
class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['quantity', 'type']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'type': forms.Select(attrs={'class': 'form-control'})
        }
        
    # Campos para la simulación de pago con tarjeta (no se guardan en la BD)
    card_number = forms.CharField(max_length=16, required=True, label='Número de Tarjeta *')
    card_holder = forms.CharField(max_length=100, required=True, label='Nombre del Titular *')
    expiration_date = forms.CharField(max_length=5, required=True, label='Expiración (MM/YY *)')
    cvc = forms.CharField(max_length=3, required=True, label='CVC *')
    
class Notification(models.Model):
    title = models.CharField(max_length=50)
    message = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    priority = models.CharField(max_length=10)
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    users = models.ManyToManyField(
        User,
        through='NotificationUser',
        related_name='notifications'
    )

    @classmethod
    def new(cls, users, event, title, message, priority):    
        notification = Notification.objects.create(
            event=event,
            title=title,
            message=message,
            priority=priority
        )
        
        notification.users.set(users)

        return notification
    
    @classmethod
    def notify_event_change(cls, event, current_user):
        users_to_notify = User.objects.filter(tickets__event=event).distinct()
        if len(users_to_notify) > 0:
            title = "Evento Modificado"
            message = "El evento ha sido modificado. Revisa el detalle del evento para mantenerte actualizado " + "<a href=/events/" + str(event.id) + ">aqui</a>"
            return Notification.new([current_user, *users_to_notify], event, title, message, "LOW")
        return None

    def update(self, users, event, title, message, priority):
        self.event = event
        self.title = title
        self.message = message
        self.priority = priority
        self.save()
        self.users.set(users)
        
    def mark_as_read(self, user_id):
        notification_user = NotificationUser.objects.filter(notification=self, user_id=user_id).first()

        if notification_user:
            notification_user.is_read = True
            notification_user.save()
    

class NotificationUser(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)

    class Meta:
        unique_together = ('notification', 'user')

CALIFICACIONES = [(i, f"{i} ⭐") for i in range(1,6)]

class Rating(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    evento = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="ratings")
    titulo = models.CharField(max_length=255)
    texto = models.TextField(blank=True)
    calificacion = models.IntegerField(choices=CALIFICACIONES) 
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        #Con unique se busca que solo el usuario pueda hacer una sola calificacion
        ordering = ['-fecha_creacion']
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'evento'], name='unique_rating')
        ]
    
    def __str__(self):
        return f'{self.usuario} - {self.evento} ({self.calificacion}⭐)'
    
    
    def update(self, titulo, calificacion, texto):
        self.titulo = titulo
        self.calificacion = calificacion
        self.texto = texto
        self.save()  

class Rating_Form(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['titulo', 'calificacion', 'texto']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Gran experiencia'
            }),
            'calificacion': forms.HiddenInput(),
            'texto': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Comparte tu experiencia...'
            }),
        }
    
class RefoundRequest(models.Model):
    REFOUND_STATES= [('pending', 'PENDIENTE'), ('approved', 'APROBADA'), ('denied', 'DENEGADA')]

    id = models.AutoField(primary_key=True)
    approved = models.CharField(choices= REFOUND_STATES, max_length=255, default= 'pending')
    approval_date = models.DateField(default=None, null=True, blank=True)
    ticket_code = models.TextField(max_length=50)
    reason = models.TextField(max_length=255)
    details= models.TextField(blank=True, max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    user_id = models.ForeignKey(User, on_delete= models.CASCADE)

    @classmethod
    def new(cls, ticket_code, reason, details, user):
        errors = RefoundRequest.validate(ticket_code, reason, details)

        if len(errors.keys()) > 0:
            return False, errors

        refound= cls.objects.create(
            ticket_code= ticket_code,
            reason=reason,
            details=details,
            user_id=user
        )

        return refound, None
    
    def update(self, ticket_code, reason, details):
        errors = RefoundRequest.validate(ticket_code, reason, details)

        if len(errors.keys()) > 0:
            return False, errors
        
        self.ticket_code = ticket_code or self.ticket_code
        self.reason = reason or self.reason
        self.details = details or self.details
        self.save()

        return True, None
    
    @classmethod
    def validate(cls, ticket_code, reason, details):
        errors = {}

        if ticket_code == "":
            errors["ticket_code"] = "Por favor ingrese un código válido"
        if not ticket_code.strip():
            errors["ticket_code"] = "Por favor ingrese un título válido"  
        if len(ticket_code)>50:
            errors["ticket_code"] = "El código no debe exceder los 50 caracteres"    

        if not reason:
            errors["reason"] = "Por favor selecciona un motivo válido."         

        if details and len(details)>255:
            errors["details"] = "El motivo no debe exceder los 255 caracteres"  

        return errors

