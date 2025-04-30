from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


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
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @classmethod
    def validate(cls, name, description, exclude_id=None):
        errors = {}

        if not name.strip():
            errors["name"] = "El nombre no puede estar vacío"
        elif cls.objects.filter(name__iexact=name).exclude(pk=exclude_id).exists():
            errors["name"] = "Ya existe una categoría con ese nombre"

        if not description.strip():
            errors["description"] = "La descripción no puede estar vacía"

        return errors

    @classmethod
    def new(cls, name, description, is_active):
        name = name.strip()
        errors = cls.validate(name, description)

        if errors:
            return False, errors

        cls.objects.create(
            name=name.strip(),
            description=description.strip(),
            is_active=is_active
        )

        return True, None

    def update(self, name, description, is_active):
        if name:
            self.name = name.strip()
        self.description = description.strip()
        self.is_active = is_active
        self.save()


class Event(models.Model):

    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    venue= models.ForeignKey('Venue', on_delete=models.SET_NULL, related_name='events', null=True, blank=True)
    categories = models.ManyToManyField(Category, blank=True)


    def __str__(self):
        return self.title

    @classmethod
    def validate(cls, title, description, scheduled_at, current_event_id=None):
        errors = {}

        if not title.strip():
            errors["title"] = "Por favor ingrese un título"
        elif cls.objects.filter(title__iexact=title).exclude(pk=current_event_id).exists():
            errors["title"] = "Ya existe un evento con ese título"

        if not description.strip():
            errors["description"] = "Por favor ingrese una descripción"

        if scheduled_at is None:
            errors["scheduled_at"] = "La fecha y hora del evento son requeridas"
        elif scheduled_at <= timezone.now():
            errors["scheduled_at"] = "La fecha del evento debe ser en el futuro"

        return errors

    @classmethod
    def new(cls, title, description, scheduled_at, organizer):
        errors = cls.validate(title, description, scheduled_at)

        if errors:
            return False, errors

        cls.objects.create(
            title=title.strip(),
            description=description.strip(),
            scheduled_at=scheduled_at,
            organizer=organizer,
        )

        return True, None

    def update(self, title, description, scheduled_at, organizer):
        errors = self.validate(title, description, scheduled_at, current_event_id=self.pk)

        if errors:
            return False, errors

        self.title = title.strip()
        self.description = description.strip()
        self.scheduled_at = scheduled_at
        self.organizer = organizer
        self.save()

class Venue(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    capacity=models.IntegerField()
    contact=models.CharField(max_length=100)
    
    @classmethod
    def new(cls, name, address, city, capacity,contact):
        errors = {}

        if len(errors.keys()) > 0:
            return False, errors

        Venue.objects.create(
            name=name,
            address=address,
            city=city,
            capacity=capacity,
            contact=contact,
        )

        return True, None
    
    def update(self, name, address, city, capacity,contact):
        self.name = name or self.name
        self.address = address or self.address
        self.city = city or self.city
        self.capacity = capacity or self.capacity
        self.contact = contact or self.contact

        self.save()

        return True, None
        