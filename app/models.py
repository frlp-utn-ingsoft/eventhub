import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

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
        """Create a new venue with validation"""
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
        return True, self
    
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

    
    def available_tickets_to_buy(self, event):
        """
        Returns the amount of tickets that the User can buy, taking into account that the max is 4.
        """

        event_tickets = self.tickets.filter(event=event)
        aux = 0

        for t in event_tickets:
            aux += t.quantity

        return max(0, 4 - aux)


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @classmethod
    def validate(cls, name, description, is_active):
        errors = {}

        if not name:
            errors["name"] = "El nombre es requerido"
        elif Category.objects.filter(name=name).exists():
            errors["name"] = "Ya existe una categoría con este nombre"

        if not description:
            errors["description"] = "La descripción es requerida"

        if is_active is None:
            errors["is_active"] = "El estado es requerido"

        return errors

    @classmethod
    def new(cls, name, description, is_active):
        errors = Category.validate(name, description, is_active)

        if len(errors.keys()) > 0:
            return False, errors

        category = Category.objects.create(
            name=name,
            description=description,
            is_active=is_active,
        )

        return True, category

    def update(self, name=None, description=None, is_active=None):
        if name and name != self.name:
            if Category.objects.filter(name=name).exists():
                return False, {"name": "Ya existe una categoría con este nombre"}
            self.name = name

        if description:
            self.description = description

        if is_active is not None:
            self.is_active = is_active

        self.save()
        return True, None


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='venues')
    attendees = models.ManyToManyField(User, related_name="attended_events", blank=True)
    categories = models.ManyToManyField(Category, related_name="events")
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
    def new(cls, title, description, scheduled_at, organizer, venue, categories=None):
        errors = Event.validate(title, description, scheduled_at)

        if len(errors.keys()) > 0:
            return False, errors

        event = Event.objects.create(
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            organizer=organizer,
            venue=venue
        )
        
        if categories:
            event.categories.set(categories)

        return True, event

    def update(self, title=None, description=None, scheduled_at=None, organizer=None, venue=None, categories=None):
        self.title = title or self.title
        self.description = description or self.description
        self.scheduled_at = scheduled_at or self.scheduled_at
        self.organizer = organizer or self.organizer
        self.venue = venue or self.venue
        
        if categories:
            self.categories.set(categories)
            
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

        if not event:
            errors["event"] = "Evento es requerido"

        if quantity is None or "":
            errors["quantity"] = "La cantidad es requerida"
        elif not isinstance(quantity, int):
            errors["quantity"] = "La cantidad debe ser un número entero válido"
        elif user.available_tickets_to_buy(event) == 0:
            errors["quantity"] = "Ya has alcanzado el límite de entradas que puedes comprar para este evento."
        elif quantity < 1:
            errors["quantity"] = "La cantidad debe ser al menos 1"
        elif quantity > 4:
            errors["quantity"] = "Puedes comprar 4 lugares como máximo."
        
        valid_types = [choice[0] for choice in cls.TICKETS_TYPE_CHOICES]
        if not type or type not in valid_types:
            errors["type"] = f"Tipo inválido. Opciones válidas: {', '.join(valid_types)}"

        
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
        return True, self
    
    def is_recent_purchase(self, minutes=30):
        """Verifica si la compra fue hace menos de X minutos"""
        return (timezone.now() - self.buy_date) < timedelta(minutes=minutes)


class Rating(models.Model):
    title = models.CharField(max_length=200, default="Calificación")
    text = models.TextField(default="Sin comentarios")
    rating = models.IntegerField(default=5)  # Valor por defecto de 5 estrellas
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ratings')

    def __str__(self):
        return f"{self.title} - {self.event.title}"

    @classmethod
    def validate(cls, score, comment):
        errors = {}
        
        if not 1 <= score <= 5:
            errors["score"] = "La calificación debe estar entre 1 y 5"
            
        if len(comment) > 500:
            errors["comment"] = "El comentario no puede tener más de 500 caracteres"
            
        return errors

    @classmethod
    def new(cls, event, user, score, comment=""):
        errors = cls.validate(score, comment)
        
        if len(errors.keys()) > 0:
            return False, errors
            
        rating = cls.objects.create(
            event=event,
            user=user,
            score=score,
            comment=comment
        )
        
        return True, rating

    def update(self, score, comment):
        errors = self.validate(score, comment)
        
        if len(errors.keys()) > 0:
            return False, errors
            
        self.score = score
        self.comment = comment
        self.save()
        
        return True, None

class Comment(models.Model):
    title = models.CharField(max_length=200)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    event = models.ForeignKey(Event,on_delete=models.CASCADE, related_name="comments") ##Muchos comentarios tienen un evento
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments") ##Muchos comentarios tienen un usuario
    
    @classmethod
    def validate(cls,title, description):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"

        if description == "":
            errors["description"] = "Por favor ingrese una descripcion"

        return errors
    
    
    @classmethod
    def new(cls,text,title,event,user):
        
        errors = Comment.validate(title, text)

        if len(errors.keys()) > 0:
            return False, errors
        
        Comment.objects.create(
            title = title,
            text = text,
            event = event,
            user = user
            )
    
    def update(self, title,text): ##self, porque es metodo de instancia / cls para clases
        self.title = title or self.title
        self.text = text or self.text
        self.save()
            
    
class Notification(models.Model):
    PRIORITY_CHOICES = [
        ("HIGH", "High"),
        ("MEDIUM", "Medium"),
        ("LOW", "Low"),
    ]

    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="LOW"
    )
    is_read = models.BooleanField(default=False)
    event = models.ForeignKey(
        "Event", on_delete=models.CASCADE, related_name="notifications"
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="notifications"
    )
    def __str__(self):
        return self.title
    
class RefundRequest(models.Model):
    approval = models.BooleanField(null=True, blank=True)
    approval_date = models.DateField(null=True, blank=True)
    ticket_code = models.CharField(max_length=255)
    reason = models.CharField(max_length=255)
    additional_details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_policy = models.BooleanField(default=False)
    event_name = models.CharField(max_length=255, blank=True, null=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="refund_requests")

    def __str__(self):
        return f"Refund Request for Ticket: {self.ticket_code}"
