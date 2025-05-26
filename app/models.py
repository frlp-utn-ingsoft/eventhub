from django.contrib.auth.models import AbstractUser
from django.db import models
from decimal import Decimal
import uuid
from django.conf import settings

class User(AbstractUser):
    is_organizer = models.BooleanField(default=False)
    eventos_favoritos = models.ManyToManyField('Event', blank=True, related_name='favorited_by')

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
    
    def marcar_evento_favorito(self, evento):
        """Marca un evento como favorito"""
        self.eventos_favoritos.add(evento)
    
    def desmarcar_evento_favorito(self, evento):
        """Desmarca un evento como favorito"""
        self.eventos_favoritos.remove(evento)
    
    def es_evento_favorito(self, evento):
        """Verifica si un evento es favorito del usuario"""
        return self.eventos_favoritos.filter(id=evento.id).exists()


class Location(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    city = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField()
    contact = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} - {self.city}"

    @classmethod
    def validate(cls, name, address, city, capacity, contact):
        errors = {}

        if not name:
            errors["name"] = "El nombre es requerido."
        
        if not address:
            errors["address"] = "La dirección es requerida."
        
        if not city:
            errors["city"] = "La ciudad es requerida."
        
        if capacity is None:
            errors["capacity"] = "La capacidad es requerida."
        elif capacity <= 0:
            errors["capacity"] = "La capacidad debe ser un número positivo."
        
        if not contact:
            errors["contact"] = "El contacto es requerido."

        return errors

    @classmethod
    def new(cls, name, address, city, capacity, contact):
        errors = cls.validate(name, address, city, capacity, contact)
        if errors:
            return False, errors

        Location.objects.create(
            name=name,
            address=address,
            city=city,
            capacity=capacity,
            contact=contact,
        )

        return True, None

    def update(self, name=None, address=None, city=None, capacity=None, contact=None):
        self.name = name or self.name
        self.address = address or self.address
        self.city = city or self.city
        self.capacity = capacity if capacity is not None else self.capacity
        self.contact = contact or self.contact

        self.save()

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    @classmethod
    def validate(cls, name, description):
        errors ={}

        if not name:
            errors["name"] = "El nombre es requerido."

        if not description:
            errors["description"] = "La descripción es requerida."
        
        return errors
    
    @classmethod
    def new(cls, name, description):
        errors = cls.validate(name, description)
        if errors:
            return False, errors

        Category.objects.create(
            name=name,
            description=description,
        )

        return True, None
    
    def update(self, name=None, description=None, is_active=None):
        self.name = name or self.name
        self.description = description or self.description

        if is_active is not None:
            self.is_active = is_active

        self.save()

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, related_name="events", null=True, blank=True)
    categories = models.ManyToManyField(Category, through='EventCategory')
    price_general = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    price_vip = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return self.title    
    
    @classmethod
    def get_price_for_type(cls, type, price_general, price_vip):
        if type == 'vip':
            return price_vip
        return price_general

    @classmethod
    def validate(cls, title, description, scheduled_at):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"

        if description == "":
            errors["description"] = "Por favor ingrese una descripcion"

        return errors

    @classmethod
    def new(cls, title, description, scheduled_at, organizer, location=None, price_general=Decimal('0.00'), price_vip=Decimal('0.00')):
        errors = Event.validate(title, description, scheduled_at)

        if len(errors.keys()) > 0:
            return False, errors

        event = Event.objects.create(
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            organizer=organizer,
            location=location,
            price_general=price_general,
            price_vip=price_vip,
        )

        return event, None

    def update(self, title, description, scheduled_at, organizer, location=None, price_general=Decimal('0.00'), price_vip=Decimal('0.00')   ):
        self.title = title or self.title
        self.description = description or self.description
        self.scheduled_at = scheduled_at or self.scheduled_at
        self.organizer = organizer or self.organizer
        self.location = location if location is not None else self.location
        self.price_general= price_general or self.price_general
        self.price_vip = price_vip or self.price_vip

        self.save()

class EventCategory(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('event', 'category')

    def __str__(self):
        return f"{self.event.title} - {self.category.name}"

class Notification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    priority = models.CharField(max_length=50, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')])
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.created_at}"
    
    @classmethod
    def validate(cls, title, message, event_id, recipient_type, specific_user_id):
        errors = {}

        if not title:
            errors["title"] = "El título es requerido."
        
        if not message:
            errors["message"] = "El mensaje es requerido."
        
        if recipient_type == "event" and not event_id:
            errors["event"] = "El evento es requerido."
        
        if recipient_type == "specific" and not specific_user_id:
            errors["user"] = "El usuario específico es requerido."

        return errors
    
    @classmethod
    def new(cls, title, message, event, priority):
        notification = Notification.objects.create(
            title=title,
            message=message,
            event=event,
            priority=priority,
        )
        return notification
    
class NotificationXUser(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name="notification_user")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_notification")
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.notification} - {self.user}"
    
    @classmethod
    def new(cls, notification, user):
        notification_user = NotificationXUser.objects.create(
            notification=notification,
            user=user,
        )
        return notification_user

class Comments(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    @classmethod
    def validate(cls, title, description):
        errors = {}

        if not title.strip():
            errors["title"] = "Por favor ingrese un título"

        if not description.strip():
            errors["description"] = "Por favor ingrese una descripción"

        return errors

    @classmethod
    def new(cls, title, description, user, event):
        errors = cls.validate(title, description)

        if errors:
            return False, errors

        comment = cls.objects.create(
            title=title,
            description=description,
            user=user,
            event=event
        )
        return True, comment

class Ticket(models.Model):
    TICKET_TYPES = [
        ('general', 'General'),
        ('vip', 'VIP'),
    ]
    CARD_TYPE_CHOICES = [
        ('credit', 'Tarjeta de Credito'),
        ('debit', 'Tarjeta de Debito'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_ticket")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="event_ticket")
    buy_date = models.DateTimeField(auto_now_add=True)
    ticket_code = models.CharField(max_length=100, unique=True, editable=False)
    quantity = models.PositiveIntegerField()
    type = models.CharField(max_length=10, choices=TICKET_TYPES)
    card_type = models.CharField(max_length=20, choices=CARD_TYPE_CHOICES)
    last4_card_number = models.CharField(max_length=4, blank=True)
    price_per_ticket = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    
    def subtotal(self):
        return self.quantity * self.price_per_ticket

    def tax(self):
        return self.subtotal() * Decimal('0.10')

    def total(self):
        return self.subtotal() + self.tax()

    def __str__(self):
        return f"{self.ticket_code} - {self.type} x{self.quantity} - {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.ticket_code:
            import uuid
            self.ticket_code = str(uuid.uuid4()).replace('-', '')[:20]
        super().save(*args, **kwargs)
        if self.event:
            if self.type == 'vip':
                self.price_per_ticket = self.event.price_vip
            else:
                self.price_per_ticket = self.event.price_general

    @classmethod
    def validate(cls, user, event, quantity, ticket_type, card_type):
        errors = {}

        if not user:
            errors["user"] = "El usuario es requerido."
        if not event:
            errors["event"] = "El evento es requerido."
        if not quantity or quantity <= 0:
            errors["quantity"] = "La cantidad debe ser mayor a cero."
        if ticket_type not in dict(cls.TICKET_TYPES):
            errors["type"] = "El tipo debe ser 'General' o 'VIP'."
        if card_type not in dict(cls.CARD_TYPE_CHOICES):
            errors["type"] = "Debe ser una tarjeta de debito o credito."


        return errors

    @classmethod
    def new(cls, user, event, quantity, ticket_type, card_type):
        errors = cls.validate(user, event, quantity, ticket_type, card_type)
        if errors:
            raise ValueError(errors)

        return cls.objects.create(
            user=user,
            event=event,
            quantity=quantity,
            type=ticket_type,
            card_type=card_type
        )
