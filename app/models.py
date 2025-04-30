from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings

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
    categories = models.ManyToManyField('Category', related_name='events')              # ADD ----- crud-category
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @classmethod
    def validate(cls, title, description, scheduled_at, categories):                    # ADD ----- crud-category
        errors = {}

        if not title:
            errors["title"] = "Por favor ingrese un título"

        if not description:
            errors["description"] = "Por favor ingrese una descripción"

        if not categories or len(categories) == 0:                                      # ADD ----- crud-category   
            errors["categories"] = "Por favor seleccione al menos una categoría"

        return errors

    @classmethod
    def new(cls, title, description, scheduled_at, organizer, categories):              # ADD ----- crud-category
        errors = Event.validate(title, description, scheduled_at, categories)

        if len(errors.keys()) > 0:
            return False, errors

        event = Event.objects.create(
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            organizer=organizer,
        )
        event.categories.set(categories)                                                        # ADD ----- crud-category
        return True, None

    def update(self, title, description, scheduled_at, organizer, categories):                  # ADD ----- crud-category
        self.title = title or self.title
        self.description = description or self.description
        self.scheduled_at = scheduled_at or self.scheduled_at
        self.organizer = organizer or self.organizer

        self.save()


class Notification(models.Model):
    PRIORITY_CHOICES = [
        ("HIGH", "Alta"),
        ("MEDIUM", "Media"),
        ("LOW", "Baja"),
    ]

    user      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title     = models.CharField(max_length=60)
    message   = models.TextField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)
    priority  = models.CharField(
        max_length=6, choices=PRIORITY_CHOICES, default="LOW"
    )
    is_read   = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} → {self.user.username}"

        if categories:
            self.categories.set(categories)             # ADD ----- crud-category


######### crud-category #########
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @classmethod
    def validate(cls, name, description):   
        errors = {}

        if name == "":
             errors["name"] = "Por favor ingrese nombre de categoria."

        if description == "":
            errors["description"] = "Por favor ingrese una descripcion"


        return errors