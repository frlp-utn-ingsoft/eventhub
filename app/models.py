import uuid
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import MaxValueValidator

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
    
class Category(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True, default="Sin descripción")
    active = models.BooleanField(default=True)
    event = models.ForeignKey(
        'app.Event',                # Ajusta 'app' al nombre real de tu app si es distinto
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='categoriesEvent'
    )
    
    def __str__(self):
        return self.name
    
    @classmethod
    def validate(cls, name, description):
        errors = {}

        if name == "":
            errors["name"] = "Por favor ingrese un titulo"

        if description == "":
            errors["description"] = "Por favor ingrese una descripcion"

        return errors
    
    @classmethod
    def new(cls, name, description, event=None, active=True):  # El evento puede ser None
        if not description:
            description = "Sin descripción"
        category = cls(name=name, description=description, event=event, active=active)
        category.save()
        return category
    
    
    def update(self , name=None, description=None, active=None, event=None): # type: ignore
        
        self.name = name or self.name
        self.description = description or self.description
        self.active = active or self.active
        self.event = event or self.event
        self.save() # type: ignore

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    categories = models.ManyToManyField('Category', related_name="event_categories", blank=True)  # Allowing nulls 
    
    venue = models.ForeignKey('Venue', on_delete=models.CASCADE, related_name='events', null=True, blank=True) ## agg fk para la relacion events / venue

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
    def new(cls, title, description, scheduled_at, organizer, venue):
        errors = Event.validate(title, description, scheduled_at)

        if len(errors.keys()) > 0:
            return False, errors

        Event.objects.create(
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            organizer=organizer,
            venue=venue,  ## agg para la relacion events / venue
        )

        return True, None

    def update(self, title, description, scheduled_at, organizer, venue):
        self.title = title or self.title
        self.description = description or self.description
        self.scheduled_at = scheduled_at or self.scheduled_at
        self.organizer = organizer or self.organizer
        self.venue = venue or self.venue ## agg para la relacion events / venue

        self.save()

class Ticket(models.Model):

    TICKET_TYPES = [
        ("GENERAL", "GENERAL"),
        ("VIP", "VIP"),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="tickets")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tickets")
    buy_date = models.DateTimeField(auto_now_add=True)
    ticket_code = models.UUIDField(default=uuid.uuid4, editable =False, unique=True)
    quantity= models.PositiveIntegerField()
    type = models.CharField(max_length=10, choices=TICKET_TYPES)

    def __str__(self):
        return f"Ticket {self.ticket_code}: {self.user} ({self.type}), Event: {self.event.title}, Quantity: {self.quantity}, Bought on: {self.buy_date}"

class Notification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add = True)
    priority = models.CharField(max_length=6,choices=[("High","High"),("Medium","Medium"),("Low","Low")])
    users = models.ManyToManyField(User, related_name= "notificaciones")
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.SET_NULL) 

    def __str__(self):
        return self.title
    
    @classmethod
    def validate(cls, title, message, priority):
        errors = {}

        if not title or not title.strip():
            errors["title"] = "El título no puede estar vacío."
        elif len(title.strip()) < 10:
            errors["title"] = "El título debe tener al menos 10 caracteres."
        elif cls.objects.filter(title=title).exists():
            errors["title"] = "Ese título ya existe."
        elif len(title.strip()) > 100:
            errors["title"] = "El título no debe superar los 100 caracteres."
        elif len(re.findall(r"[a-zA-Z]", title)) < 10:
            errors["title"] = "El título debe contener al menos 10 letras."

        if not message or not message.strip():
            errors["message"] = "El mensaje no puede estar vacío."
        elif len(message.strip()) < 10:
            errors["message"] = "El mensaje debe tener al menos 10 caracteres."
        elif len(message.strip()) > 500:
            errors["message"] = "El mensaje no debe superar los 500 caracteres."
        elif len(re.findall(r"[a-zA-Z]", message)) < 10:
            errors["message"] = "El mensaje debe contener al menos 10 letras."

        if priority not in ["High", "Medium", "Low"]:
            errors["priority"] = "Prioridad inválida."

        return errors

    @classmethod
    def new(cls, title, message, priority, event=None, users=None):
        errors = cls.validate(title, message, priority)

        user_ids = set()

        if event:
            user_ids.update(
                Ticket.objects.filter(event=event)
                .values_list("user_id", flat=True)
            )

        if users:
            if isinstance(users, list):
                user_ids.update([u.id for u in users])
            else:
                user_ids.add(users.id)

        if not user_ids:
            errors["users"] = "Debes asignar al menos un usuario o evento con asistentes."

        if errors:
            return False, errors

        notification = cls.objects.create(
            title=title,
            message=message,
            priority=priority,
            event=event
        )

        final_users = User.objects.filter(id__in=user_ids)
        notification.users.add(*final_users)

        for user in final_users:
            User_Notification.objects.create(user=user, notification=notification)

        return True, notification


class Rating(models.Model):
    title = models.CharField(max_length=255)
    text = models.TextField()
    rating = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,related_name="rating",null=True,blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="rating", null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.rating/5})"
    
    @classmethod
    def validate(cls,title,text,rating):
        errors = {}

        if not title:
            errors["title"] = "El título no puede estar vacío."
        if not text:
            errors["text"] = "El texto no puede estar vacío."
        if rating is None or not (1 <= rating <= 5):
            errors["rating"] = "El rating debe ser un número entre 1 y 5."

        return errors
    @classmethod
    def new(cls, title, text, rating, user=None, event=None):
        errors = cls.validate(title, text, rating)

        if errors:
            return False, errors

        rating_obj = cls.objects.create(
            title=title,
            text=text,
            rating=rating,
            user=user,
            event=event
        )
        return True, rating_obj

    def update(self, title, text, rating):
        errors = Rating.validate(title, text, rating)
        if errors:
            return False, errors

        self.title = title or self.title
        self.text = text or self.text
        self.rating = rating or self.rating
        self.save()
        return True, None

class Comment(models.Model):
    tittle = models.CharField(max_length=255)
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comment',
        null=True
    )

    event = models.ForeignKey(
        'app.Event',
        on_delete=models.CASCADE,
        related_name='comment',
        null=True
    )

    def __str__(self):
        return f"{self.tittle} - {self.user}"


class User_Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification = models.ForeignKey("Notification", on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    class Meta:
        unique_together = ('user', 'notification')

    def __str__(self):
        return f"{self.user.username} - {self.notification.title}"

class Venue(models.Model):
    name = models.CharField(max_length=25)
    address = models.CharField(max_length=30)
    city = models.CharField(max_length=25)
    capacity = models.PositiveIntegerField(validators=[MaxValueValidator(300000)])
    contact = models.TextField(max_length=200)

    def __str__(self):
        return f"{self.name} | {self.address}, {self.city} | Capacidad: {self.capacity} | Contacto: {self.contact}"

class RefundRequest(models.Model):
    approved = models.BooleanField(null=True, blank=True)
    approval_date = models.DateField(null=True, blank=True)
    ticket_code = models.CharField(max_length=50)
    reason = models.CharField(max_length=255)
    created_at = models.DateField(auto_now_add=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="RefundRequest")

    def __str__(self):
        return f"{self.ticket_code} - {self.user.username}"
    
    def get_status_display(self):
        if self.approved is None:
                return "Pendiente"
        return "Aprobado" if self.approved else "Rechazado"
    
    @classmethod
    def validate(cls, ticket_code, reason):
        errors = {}

        if not ticket_code:
            errors["ticket_code"] = "El código de ticket no puede estar vacío."

        if not reason:
            errors["reason"] = "El motivo no puede estar vacío."

        return errors

    @classmethod
    def new(cls, ticket_code, reason, user, approved=False, approval_date=None, created_at=None):
        errors = cls.validate(ticket_code, reason)

        if errors:
            return False, errors

        refund = cls(
            ticket_code=ticket_code,
            reason=reason,
            user=user,
            approved=approved,
            approval_date=approval_date,
            created_at=created_at
        )
        refund.save()
        return True, refund

    @classmethod
    def update(cls, refund_id, ticket_code=None, reason=None, approved=None, approval_date=None):
        try:
            refund = cls.objects.get(id=refund_id)

            # Si te pasan ticket_code o reason, validás.
            if ticket_code is not None or reason is not None:
                errors = cls.validate(ticket_code or refund.ticket_code, reason or refund.reason)
                if errors:
                    return False, errors

            if ticket_code is not None:
                refund.ticket_code = ticket_code
            if reason is not None:
                refund.reason = reason
            if approved is not None:
                refund.approved = approved
            if approval_date is not None:
                refund.approval_date = approval_date

            refund.save()
            return True, refund

        except cls.DoesNotExist:
            return False, "Solicitud de reembolso no encontrada."

    @classmethod
    def delete_id(cls, refund_id):
        try:
            refund = cls.objects.get(id=refund_id)
            refund.delete()
            return True, "Solicitud de reembolso eliminada correctamente."

        except cls.DoesNotExist:
            return False, "Solicitud de reembolso no encontrada."
        

    @classmethod
    def has_pending_request(cls, user):
        return cls.objects.filter(user=user, approved__isnull=True).exists()

class FavoriteEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey('Event', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

class Meta:
    unique_together = ('user', 'event')  # evita duplicados


class SurveyResponse(models.Model):
    ticket = models.OneToOneField('Ticket', on_delete=models.CASCADE)
    satisfaction = models.IntegerField()
    issue = models.TextField(blank=True, null=True)
    recommend = models.BooleanField()
    submitted_at = models.DateTimeField(auto_now_add=True)
