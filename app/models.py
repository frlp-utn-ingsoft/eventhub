import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator

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

class Ticket(models.Model):
    # Constants
    GENERAL = 'GENERAL'
    VIP = 'VIP'
    TICKETS_TYPE_CHOICES = [
        (GENERAL, 'General'),
        (VIP, 'VIP')
    ]

    # Atributes
    buy_date = models.DateTimeField(verbose_name = 'Fecha de compra')
    ticket_code = models.models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='Código del ticket'
    ),
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name = 'Cantidad')
    type = models.CharField(max_length=25, choices=TICKETS_TYPE_CHOICES, verbose_name = 'Tipo de ticket')

    # Foreign keys
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tickets')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')

    # Meta class
    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        # Default ordering: newest tickets first
        ordering = ['-buy_date']

    # Methods
    def __str__(self):
        return f"{self.ticket_code} - {self.get_type_display()} ({self.quantity})"
    
    @classmethod
    def validate(cls, buy_date, ticket_code, quantity, type, event, user):
        """Validate ticket data before creation"""
        errors = {}

        if not buy_date:
            errors["buy_date"] = "Por favor ingrese una fecha de compra"

        if not ticket_code or not ticket_code.strip():
            errors["ticket_code"] = "Por favor ingrese un código para el ticket"

        if not quantity or quantity < 1:
            errors["quantity"] = "Por favor ingrese una cantidad válida (mínimo 1)"
        
        if not type or type not in dict(cls.TICKET_TYPE_CHOICES).keys():
            errors["type"] = "Por favor seleccione un tipo válido"
        
        if not event:
            errors["event"] = "Por favor seleccione un evento"
        
        if not user:
            errors["user"] = "Por favor seleccione un usuario"
        
        return errors
    
    @classmethod
    def new(cls, buy_date, ticket_code, quantity, type, event, user):
        """Create a new ticket with validation"""
        errors = cls.validate(buy_date, quantity, type, event, user)

        if errors:
            return False, errors

        ticket = cls.objects.create(
            buy_date = buy_date,
            quantity = quantity,
            type = type,
            event = event,
            user = user
        )

        return True, ticket

    def update(self, buy_date, ticket_code, quantity, type, event, user):
        """Update ticket fields"""
        if buy_date is not None:
            self.buy_date = buy_date
        if ticket_code is not None:
            self.ticket_code = ticket_code
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