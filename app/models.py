from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    used = models.BooleanField(default=False)
    refunded = models.BooleanField(default=False)
    purchased_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"

class RefundRequest(models.Model):
    STATUS_PENDING = "P"
    STATUS_APPROVED = "A"
    STATUS_REJECTED = "R"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pendiente"),
        (STATUS_APPROVED, "Aprobada"),
        (STATUS_REJECTED, "Rechazada"),
    ]

    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE)
    reason = models.TextField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Solicitud de reembolso para #{self.pk} - Estado: {self.get_status_display()}"
    
    def is_valid_for_refund(self):
        # Comprueba si la solicitud de reembolso es válida, si no esta usado, ni expirado (pasados los 30 dias), ni ya reembolsado
        if self.ticket.used:
            return False
        if self.ticket.refunded:
            return False
        event_date = self.ticket.event.scheduled_at
        if timezone.now() > event_date + timedelta(days=30):
            return False
        return True
    
    @property
    def user(self):
        return self.ticket.user