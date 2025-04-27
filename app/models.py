from django.contrib.auth.models import AbstractUser
from django.db import models


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


#comentarios
class Comment(models.Model):
    title = models.CharField(max_length=200)
    text = models.CharField(max_length=140)
    created_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="comments")

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    @classmethod
    def validate(cls, title, text):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"
        if len(title)>200:
            errors["title"] = "El título no debe exceder los 200 caracteres" 
        if not title.strip():
            errors["title"] = "Por favor ingrese un título válido"      

        if text == "":
            errors["text"] = "Por favor ingrese un mensaje"
        if len(text)>140:
            errors["text"] = "El comentario no debe exceder los 140 caracteres"  
        if not text.strip():
            errors["text"] = "Por favor ingrese un comentario válido"     

        return errors

    @classmethod
    def new(cls, title, text, user, event):
        errors = Comment.validate(title, text)

        if len(errors.keys()) > 0:
            return False, errors

        Comment.objects.create(
            title=title,
            text=text,
            user=user,
            event=event
        )

        return True, None

    def update(self, title, text):
        errors = Comment.validate(title, text)

        if len(errors.keys()) > 0:
            return False, errors
        
        self.title = title or self.title
        self.text = text or self.text
        self.save()

        return True, None