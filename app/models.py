import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import timedelta

class Venue(models.Model):
    # Atributes
    name = models.CharField(max_length=255, verbose_name = 'Nombre')
    adress = models.CharField(max_length=255, verbose_name = 'Dirección')
    city = models.CharField(max_length=255, verbose_name = 'Ciudad')
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name = 'Capacidad')
    contact = models.CharField(max_length=255, verbose_name = 'Contacto')

    # Meta class
    class Meta:
        verbose_name = 'Venue'
        verbose_name_plural = 'Venues'
        ordering = ['-name']

    # Methods
    def __str__(self):
        return f"{self.name}"
    
    @classmethod
    def validate(cls, name, adress, city, capacity, contact):
        """Validate venue data before creation"""
        errors = {}

        if not name or len(name) == 0:
            errors["name"] = "Por favor ingrese un nombre"
        
        if not adress or len(adress) == 0:
            errors["adress"] = "Por favor ingrese una dirección"
        
        if not city or len(city) == 0:
            errors["city"] = "Por favor ingrese una ciudad"
        
        if not capacity or capacity < 1:
            errors["capacity"] = "Por favor ingrese una capacidad válida (capacidad > 1)"
        
        if not contact or len(contact) == 0:
            errors["contact"] = "Por favor ingrese un contacto"
        
        return errors
    
    @classmethod
    def new(cls, name, adress, city, capacity, contact):
        """Create a new ticketvenue with validation"""
        errors = cls.validate(name, adress, city, capacity, contact)

        if errors:
            return False, errors

        venue = cls.objects.create(
            name = name,
            adress = adress,
            city = city,
            capacity = capacity,
            contact = contact
        )

        return True, venue

    def update(self, name, adress, city, capacity, contact):
        """Update venue fields"""
        
        if name is not None and len(name) != 0:
            self.name = name
        if adress is not None and len(adress) != 0:
            self.adress = adress
        if city is not None and len(city) != 0:
            self.city = city
        if capacity is not None and capacity >= 1:
            self.capacity = capacity
        if contact is not None and len(contact) != 0:
            self.contact = contact
        
        self.save()
        return self
    
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


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='venues')

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
    def new(cls, title, description, scheduled_at, organizer):
        errors = Event.validate(title, description, scheduled_at)

        if len(errors.keys()) > 0:
            return False, errors

        Event.objects.create(
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            organizer=organizer,
        )

        return True, None

    def update(self, title, description, scheduled_at, organizer):
        self.title = title or self.title
        self.description = description or self.description
        self.scheduled_at = scheduled_at or self.scheduled_at
        self.organizer = organizer or self.organizer

        self.save()
    
   
    def available_tickets(self):
        aux = 0

        for t in self.tickets.all():
            aux = aux + t.quantity

        return self.venue.capacity - aux

class Ticket(models.Model):
    # Constants
    GENERAL = 'GENERAL'
    VIP = 'VIP'
    TICKETS_TYPE_CHOICES = [
        (GENERAL, 'General'),
        (VIP, 'VIP')
    ]

    # Atributes
    buy_date = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de compra'
    )
    ticket_code = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='Código del ticket'
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Cantidad'
    )
    type = models.CharField(
        max_length=25,
        choices=TICKETS_TYPE_CHOICES,
        verbose_name='Tipo de ticket'
    )

    # Foreign keys
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='tickets'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tickets'
    )

    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ['-buy_date']

    def __str__(self):
        return str(self.ticket_code)
    
    @classmethod
    def validate(cls, quantity, type, event, user):
        """Validate ticket data before creation"""
        errors = {}

        if quantity is None:
            errors["quantity"] = "La cantidad es requerida"
        elif not isinstance(quantity, int) or isinstance(quantity, bool):
            errors["quantity"] = "La cantidad debe ser un número entero válido"
        elif quantity < 1:
            errors["quantity"] = "La cantidad debe ser al menos 1"
        
        valid_types = [choice[0] for choice in cls.TICKETS_TYPE_CHOICES]
        if not type or type not in valid_types:
            errors["type"] = f"Tipo inválido. Opciones válidas: {', '.join(valid_types)}"
        
        if not event:
            errors["event"] = "Evento es requerido"
        
        if not user:
            errors["user"] = "Usuario es requerido"
        
        return errors
    
    @classmethod
    def new(cls, quantity, type, event, user):
        """Create a new ticket with validation"""
        errors = cls.validate(quantity, type, event, user)

        if errors:
            return False, errors

        try:
            ticket = cls.objects.create(
                quantity=quantity,
                type=type,
                event=event,
                user=user
            )

            print(ticket)
            return True, ticket
        except Exception as e:
            return False, {"error": f"Error al crear ticket: {str(e)}"}

    def update(self, buy_date, quantity, type, event, user):
        """Update ticket fields"""
        if buy_date is not None:
            self.buy_date = buy_date
        if quantity is not None:
            self.quantity = quantity
        if type is not None:
            self.type = type
        if event is not None:
            self.event = event
        if user is not None:
            self.user = user
        
        self.save()
        return self
    
    def is_recent_purchase(self, minutes=30):
        """Verifica si la compra fue hace menos de X minutos"""
        return (timezone.now() - self.buy_date) < timedelta(minutes=minutes)