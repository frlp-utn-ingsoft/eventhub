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
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    users = models.ManyToManyField(
        User,
        through='NotificationUser',
        related_name='notifications'
    )

    @classmethod
    def new(cls, users, event, title, message, priority):    
        notification = Notification.objects.create(
            event=event,
            title=title,
            message=message,
            priority=priority
        )
        
        notification.users.set(users)

        return notification
    
    def update(self, users, event, title, message, priority):
        self.event = event
        self.title = title
        self.message = message
        self.priority = priority
        self.save()
        self.users.set(users)
        
    @save
    def mark_as_read(self):
        self.is_read=True

class NotificationUser(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)

    class Meta:
        unique_together = ('notification', 'user')