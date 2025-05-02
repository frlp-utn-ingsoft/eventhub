from django.contrib.auth.models import AbstractUser
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

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Venue(models.Model):
    name = models.CharField("Nombre", max_length=100)
    address = models.CharField("Dirección", max_length=200)
    city = models.CharField("Ciudad", max_length=100)
    capacity = models.PositiveIntegerField("Capacidad")
    contact = models.TextField("Información de contacto")
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    categories = models.ManyToManyField('Category', related_name='events', blank=True)
    venue = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @classmethod
    def validate(cls, title, description, scheduled_at):
        errors = {}

        if title == "":
            errors["title"] = "Por favor, ingrese un título"

        if description == "":
            errors["description"] = "Por favor, ingrese una descripción"

        return errors
    
    @classmethod
    def new(cls, title, description, scheduled_at, organizer, venue=None, categories=None):
        errors = cls.validate(title, description, scheduled_at)

        if errors:
            return None, errors

        event = cls.objects.create(
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            organizer=organizer,
            venue=venue,
        )
        if categories:
            event.categories.set(categories)
        return event, {}


def update(self, title, description, scheduled_at, organizer, venue=None, categories=None):
    self.title = title or self.title
    self.description = description or self.description
    self.scheduled_at = scheduled_at or self.scheduled_at
    self.organizer = organizer or self.organizer
    self.venue = venue or self.venue
    self.save()

    if categories is not None:
        self.categories.set(categories)
    return self


class Rating(models.Model):
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    comment = models.TextField(blank=True, null=True)
    score = models.PositiveSmallIntegerField() 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.score} estrellas"
