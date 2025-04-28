from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django import forms
from django.utils import timezone
from django_countries.fields import CountryField
from cities_light.models import City

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
    def new(cls, title, description, scheduled_at, organizer, categories=None, venue=None):
        # Validaciones y creación
        event = cls.objects.create(
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            organizer=organizer,
            venue=venue
        )
        if categories:
            event.categories.set(categories)
        return True, event

    def update(self, title, description, scheduled_at, organizer):
        self.title = title or self.title
        self.description = description or self.description
        self.scheduled_at = scheduled_at or self.scheduled_at
        self.organizer = organizer or self.organizer

        self.save()


class Ticket(models.Model):
    TICKET_TYPES= [('general', 'General'), ('vip', 'VIP')]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tickets")
    buy_date = models.DateTimeField(auto_now_add=True)
    ticket_code = models.CharField(max_length=100, unique=True, editable=False)
    quantity = models.PositiveIntegerField(default=1)
    type = models.CharField(max_length=10, choices=TICKET_TYPES, default='general')

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
        
    # Campos para la simulación de pago con tarjeta (no se guardan en la BD)
    card_number = forms.CharField(max_length=16, required=True, label='Número de Tarjeta')
    card_holder = forms.CharField(max_length=100, required=True, label='Nombre del Titular')
    expiration_date = forms.CharField(max_length=5, required=True, label='Expiración (MM/YY)')
    cvc = forms.CharField(max_length=3, required=True, label='CVC')
    
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






