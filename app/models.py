from django.db import models
from django.utils import timezone
import uuid
from typing import Dict
from django.contrib.auth.models import AbstractUser



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
    
    class TicketType(models.TextChoices):
        GENERAL = 'GENERAL', 'General'
        VIP = 'VIP', 'VIP'
    
    buy_date = models.DateField(auto_now_add=True)
    ticket_dot = models.CharField(max_length=100, unique=True)
    quantity = models.PositiveIntegerField(default=1)
    type = models.CharField(
        max_length=7,
        choices=TicketType.choices,
        default=TicketType.GENERAL
    )
    
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name="tickets")
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name="tickets")

    def __str__(self):
        type_map = {
            'GENERAL': 'General',
            'VIP': 'VIP'
        }
        return f"{type_map.get(self.type, self.type)} Ticket - {self.event.title} (x{self.quantity})"

    def clean(self):
        errors: Dict[str, str] = {}
        
        if self.quantity <= 0:
            errors['quantity'] = 'La cantidad debe ser mayor a cero'
        
        if self.type == self.TicketType.VIP and self.quantity > 2:
            errors['type'] = 'Máximo 2 tickets VIP por compra'
        
        if self.pk and (timezone.now().date() - self.buy_date).days > 30:
            errors['buy_date'] = 'No se puede modificar después de 30 días'

    def save(self, *args, **kwargs):
        if not self.ticket_dot:
            self.ticket_dot = str(uuid.uuid4())
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_refundable(self) -> bool:
        event_date = self.event.scheduled_at.date()
        return (timezone.now().date() - event_date).days <= 30

    @classmethod
    def create_ticket(cls, user, event, quantity=1, ticket_type='GENERAL'):
        ticket = cls(
            user=user,
            event=event,
            quantity=quantity,
            type=ticket_type
        )
        ticket.full_clean()
        ticket.save()
        return ticket
