from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now


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
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tickets")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets")
    ticket_type = models.ForeignKey("TicketType", on_delete=models.CASCADE, related_name="tickets")
    ticket_code = models.CharField(max_length=50, unique=True, blank=True)
    buy_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    old_total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    @classmethod
    def validate(cls, event, user, ticket_type, quantity):
        errors = {}

        if event is None:
            errors["event"] = "El evento es requerido"
        
        if user is None:
            errors["user"] = "El usuario es requerido"
        
        if ticket_type is None:
            errors["ticket_type"] = "El tipo de ticket es requerido"

        if quantity is None or quantity <= 0:
            errors["quantity"] = "La cantidad de tickets debe ser mayor a 0"
        
        return errors
    
    @classmethod
    def new(cls, event, user, ticket_type, quantity):
        errors = Ticket.validate(event, user, ticket_type, quantity)

        if len(errors.keys()) > 0:
            return False, errors

        ticket = Ticket.objects.create(
            event=event,
            user=user,
            ticket_type=ticket_type,
            quantity=quantity,
            total_price=ticket_type.price * quantity
        )
        ticket.ticket_code = str(ticket.id) #Figura como error, pero al crear ejectuar Ticket.create() se genera id, por lo que deberia poder copiarlo en ticket_code
        ticket.save()

        return True, None
    
    def update(self, event, ticket_type, quantity):
        if quantity < 0:
            return False, {"quantity": "La cantidad de tickets debe ser mayor a 0"}
        
        self.event = event or self.event
        self.ticket_type = ticket_type or self.ticket_type
        self.quantity = quantity or self.quantity
        if quantity is not None or ticket_type is not None:
            self.old_total_price = self.total_price
            self.total_price = ticket_type.price * self.quantity
        self.modified_date = now()
        self.save()

        return True, None

class TicketType(models.Model):
    name = models.CharField(max_length=25)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @classmethod
    def validate(cls, name, price):
        errors = {}

        if name == "":
            errors["name"] = "El nombre es requerido"

        if price is None or price <= 0:
            errors["price"] = "El precio debe ser mayor a 0"

        return errors

    @classmethod
    def new(cls, name, price):
        errors = TicketType.validate(name, price)

        if len(errors.keys()) > 0:
            return False, errors

        TicketType.objects.create(
            name=name,
            price=price,
        )

        return True, None

    def update(self, price):
        errors=TicketType.validate(self.name, price)
        if len(errors.keys()) > 0:
            return False, errors
        self.price = price
        self.save()

        return True, None