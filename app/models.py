from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import datetime


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
    category = models.ForeignKey('Category', on_delete=models.PROTECT, related_name="events", null=True, blank=True)
    venue = models.ForeignKey('Venue', on_delete=models.CASCADE, related_name='events', null=True, blank=True)

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
    def new(cls, title, description, scheduled_at, organizer,category=None,venue=None):
        errors = Event.validate(title, description, scheduled_at)

        if len(errors.keys()) > 0:
            return False, errors

        Event.objects.create(
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            organizer=organizer,
            category=category,
            venue=venue,
        )

        return True, None

    def update(self, title, description, scheduled_at, organizer, category=None, venue=None):
        self.title = title or self.title
        self.description = description or self.description
        self.scheduled_at = scheduled_at or self.scheduled_at
        self.organizer = organizer or self.organizer
        self.category = category if category is not None else self.category
        self.venue = venue if venue is not None else self.venue

        self.save()

class Category(models.Model):
    name =models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    @classmethod
    def validate(cls, name, description):
        errors = {}

        if name == "":
            errors["name"] = "Por favor ingrese un nombre"

        if description == "":
            errors["description"] = "Por favor ingrese una descripcion"

        return errors

    @classmethod
    def new(cls, name, description):
        errors = Category.validate(name, description)

        if len(errors.keys()) > 0:
            return False, errors

        Category.objects.create(
            name=name,
            description=description,
        )

        return True, None
    def update(self, name, description):
        self.name = name or self.name
        self.description = description or self.description

        self.save()

class Comment(models.Model):
    title = models.CharField(max_length=100)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="comments")

    @classmethod
    def validate(cls, title, text):
        errors = {}

        if not title or title.strip() == "":
            errors["title"] = "El título es requerido"

        if not text or text.strip() == "":
            errors["text"] = "El texto es requerido"

        return errors

    @classmethod
    def new(cls, title, text, user, event):
        errors = cls.validate(title, text)

        if errors:
            return False, errors

        cls.objects.create(
            title=title.strip(),
            text=text.strip(),
            user=user,
            event=event
        )

        return True, None

    def update(self, title, text):
        self.title = title.strip() if title else self.title
        self.text = text.strip() if text else self.text
        self.save()

class Venue(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    capacity = models.IntegerField(blank=True, null=True)  # Cambiar a IntegerField
    contact = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name


class Ticket(models.Model):
    buy_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tickets")
    ticket_code = models.CharField(max_length=100, unique=True)
    quantity = models.IntegerField(default=1)
    type = models.CharField(max_length=50, choices=[('general', 'General'), ('vip', 'VIP')], default='general')

    @classmethod
    def validate(cls, ticket_code, quantity):
        errors = {}

        if ticket_code is None or ticket_code == "":
            errors["ticket_code"] = "El código de entrada es requerido"

        if quantity is None or quantity <= 0:
            errors["quantity"] = "La cantidad debe ser mayor a 0"

        return errors

    @classmethod
    def new(cls, ticket_code, quantity, user, event):
        errors = cls.validate(ticket_code, quantity)

        if len(errors.keys()) > 0:
            return False, errors

        Ticket.objects.create(
            ticket_code=ticket_code,
            quantity=quantity,
            user=user,
            event=event
        )
        return True, None

    def update(self, ticket_code, quantity):
        self.ticket_code = ticket_code or self.ticket_code
        self.quantity = quantity or self.quantity

        self.save()

class Rating(models.Model):
    title = models.CharField(max_length=100)
    text = models.TextField()
    rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ratings")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="ratings")

    @classmethod
    def validate(cls, rating,title):
        errors = {}

        if rating is None:
            errors["rating"] = "La calificación es requerida"
        elif rating < 1 or rating > 5:
            errors["rating"] = "La calificación debe estar entre 1 y 5"

        if title is None or title.strip() == "":
            errors["title"] = "El título es requerido"



        return errors

    @classmethod
    def new(cls, title, text, rating, user, event):
        errors = cls.validate(rating, title)

        if errors:
            return False, errors

        cls.objects.create(
            title=title,
            text=text,
            rating=rating,
            user=user,
            event=event
        )

        return True, None

    def update(self, rating, title, text):
        self.rating = rating if rating is not None else self.rating
        self.title = title.strip() if title else self.title
        self.text = text.strip() if text else self.text
        self.save()


class RefundStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    APPROVED = "approved", "Aprobado"
    REJECTED = "rejected", "Rechazado"

class RefundReason(models.TextChoices):
    EVENT_CANCELLED = "event_cancelled", "Evento cancelado"
    TICKET_NOT_RECEIVED = "ticket_not_received", "Entrada no recibida"
    OTHER = "other", "Otro"

class RefundRequest(models.Model):
    approved = models.BooleanField(default=False)
    approval_date = models.DateTimeField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=RefundStatus.choices, default=RefundStatus.PENDING)
    refund_reason = models.CharField(max_length=50, choices=RefundReason.choices, default=RefundReason.OTHER)
    ticket_code = models.CharField(max_length=100, unique=True)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="refund_requests", null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="refund_requests")
    created_at = models.DateTimeField(auto_now_add=True)


    @classmethod
    def new(cls, amount, reason, refund_reason, ticket_code, user, status):
        errors = cls.validate(amount, reason, status, refund_reason, ticket_code, user)

        if errors:
            return False, errors

        cls.objects.create(
            amount=amount,
            reason=reason,
            refund_reason=refund_reason,
            ticket_code=ticket_code,
            user=user,
            status=status,
            ticket=Ticket.objects.get(ticket_code=ticket_code)
        )

        return True, None

    @classmethod
    def validate(cls, amount, reason, status, refund_reason, ticket_code, user):
        errors = {}

        if amount is None or amount < 0:
            errors["amount"] = "El monto debe ser mayor a 0."

        if reason is None or reason.strip() == "":
            errors["reason"] = "La razón es requerida."
        elif len(reason) > 500:
            errors["reason"] = "La razón no puede superar los 500 caracteres."

        if status not in RefundStatus.values:
            errors["status"] = "Estado inválido."

        if refund_reason not in RefundReason.values:
            errors["refund_reason"] = "Motivo de reembolso inválido."

        if ticket_code is None:
            errors["ticket_code"] = "Debe asociarse un ticket."
        elif not Ticket.objects.filter(ticket_code=ticket_code).exists():
            errors["ticket_code"] = "El ticket no existe."

        if user is None:
            errors["user"] = "Debe asociarse un usuario."
        elif not User.objects.filter(id=user.id).exists():
            errors["user"] = "El usuario no existe."

        return errors

