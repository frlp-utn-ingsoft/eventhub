from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
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
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @classmethod
    def validate(cls, name, description, is_active):
        errors = {}

        if not name:
            errors["name"] = "El nombre es requerido"
        elif Category.objects.filter(name=name).exists():
            errors["name"] = "Ya existe una categoría con este nombre"

        if not description:
            errors["description"] = "La descripción es requerida"

        if is_active is None:
            errors["is_active"] = "El estado es requerido"

        return errors

    @classmethod
    def new(cls, name, description, is_active):
        errors = Category.validate(name, description, is_active)

        if len(errors.keys()) > 0:
            return False, errors

        category = Category.objects.create(
            name=name,
            description=description,
            is_active=is_active,
        )

        return True, None

    def update(self, name=None, description=None, is_active=None):
        if name and name != self.name:
            if Category.objects.filter(name=name).exists():
                return False, {"name": "Ya existe una categoría con este nombre"}
            self.name = name

        if description:
            self.description = description

        if is_active is not None:
            self.is_active = is_active

        self.save()
        return True, None


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    attendees = models.ManyToManyField(User, related_name="attended_events", blank=True)
    categories = models.ManyToManyField(Category, related_name="events")
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
    def new(cls, title, description, scheduled_at, organizer, categories=None):
        errors = Event.validate(title, description, scheduled_at)

        if len(errors.keys()) > 0:
            return False, errors

        event = Event.objects.create(
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            organizer=organizer,
        )
        
        if categories:
            event.categories.set(categories)

        return True, None

    def update(self, title=None, description=None, scheduled_at=None, organizer=None, categories=None):
        self.title = title or self.title
        self.description = description or self.description
        self.scheduled_at = scheduled_at or self.scheduled_at
        self.organizer = organizer or self.organizer

        self.save()


class Rating(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ratings")
    score = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['event', 'user']

    def __str__(self):
        return f"Calificación de {self.user.username} para {self.event.title}"

    @classmethod
    def validate(cls, score, comment):
        errors = {}
        
        if not 1 <= score <= 5:
            errors["score"] = "La calificación debe estar entre 1 y 5"
            
        if len(comment) > 500:
            errors["comment"] = "El comentario no puede tener más de 500 caracteres"
            
        return errors

    @classmethod
    def new(cls, event, user, score, comment=""):
        errors = cls.validate(score, comment)
        
        if len(errors.keys()) > 0:
            return False, errors
            
        rating = cls.objects.create(
            event=event,
            user=user,
            score=score,
            comment=comment
        )
        
        return True, rating

    def update(self, score, comment):
        errors = self.validate(score, comment)
        
        if len(errors.keys()) > 0:
            return False, errors
            
        self.score = score
        self.comment = comment
        self.save()
        
        return True, None
class Comment(models.Model):
    title = models.CharField(max_length=200)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    event = models.ForeignKey(Event,on_delete=models.CASCADE, related_name="comments") ##Muchos comentarios tienen un evento
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments") ##Muchos comentarios tienen un usuario
    
    @classmethod
    def validate(cls,title, description):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"

        if description == "":
            errors["description"] = "Por favor ingrese una descripcion"

        return errors
    
    
    @classmethod
    def new(cls,text,title,event,user):
        
        errors = Comment.validate(title, text)

        if len(errors.keys()) > 0:
            return False, errors
        
        Comment.objects.create(
            title = title,
            text = text,
            event = event,
            user = user
            )
    
    def update(self, title,text): ##self, porque es metodo de instancia / cls para clases
        self.title = title or self.title
        self.text = text or self.text
        self.save()
            
    
class Notification(models.Model):
    PRIORITY_CHOICES = [
        ("HIGH", "High"),
        ("MEDIUM", "Medium"),
        ("LOW", "Low"),
    ]

    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="LOW"
    )
    is_read = models.BooleanField(default=False)
    event = models.ForeignKey(
        "Event", on_delete=models.CASCADE, related_name="notifications"
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="notifications"
    )
    def __str__(self):
        return self.title
