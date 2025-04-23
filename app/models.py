from django.contrib.auth.models import AbstractUser
from django.db import models

def save(method):
    def wrapper(self, *args, **kwargs):
        result = method(self, *args, **kwargs)
        self.save()
        return result
    return wrapper

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

class Notification(models.Model):
    title = models.CharField(max_length=50)
    message = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    priority = models.CharField(max_length=10)
    is_read = models.BooleanField(default=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )

    @classmethod
    def new(cls, user, title, message, created_at, priority):
        
        errors = Notification.validate(title, message, priority)

        if len(errors.keys()) > 0:
            return False, errors

        Notification.objects.create(
            user=user,
            title=title,
            message=message,
            created_at=created_at,
            priority=priority,
            is_read=False,
        )

        return True, None
    
    @classmethod
    def validate(cls, title, message, priority):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"

        titleMaxLen = 50
        if len(title) > titleMaxLen:
            errors["title"] = "Maximo " + str(titleMaxLen) + " caracteres"

        if message == "":
            errors["message"] = "Por favor ingrese una mensaje"

        messageMaxLen = 100
        if len(message) > messageMaxLen:
            errors["title"] = "Maximo " + str(messageMaxLen) + " caracteres"

        if priority == "":
            errors["priority"] = "Por favor seleccione una prioridad"

        optionList = ["LOW", "MEDIUM", "HIGH"]
        if priority not in optionList:
            errors["priority"] = "La prioridad debe ser Baja, Media o Alta"

        return errors

    @save
    def mark_as_read(self):
        self.is_read=True
