import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Ticket, Rating


class Venue(models.Model):
    # Atributes
    name = models.CharField(max_length=255, verbose_name = 'Nombre')
    adress = models.CharField(max_length=255, verbose_name = 'Dirección')
    city = models.CharField(max_length=255, verbose_name = 'Ciudad')
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name = 'Capacidad')
    contact = models.CharField(max_length=255, verbose_name = 'Contacto')

    # Meta class
    class Meta:
        verbose_name = 'Venue'
        verbose_name_plural = 'Venues'
        ordering = ['-name']

    # Methods
    def __str__(self):
        return f"{self.name}"
    
    @classmethod
    def validate(cls, name, adress, city, capacity, contact):
        """Validate venue data before creation"""
        errors = {}

        if not name or len(name) == 0:
            errors["name"] = "Por favor ingrese un nombre"
        
        if not adress or len(adress) == 0:
            errors["adress"] = "Por favor ingrese una dirección"
        
        if not city or len(city) == 0:
            errors["city"] = "Por favor ingrese una ciudad"
        
        if not capacity or capacity < 1:
            errors["capacity"] = "Por favor ingrese una capacidad válida (capacidad > 1)"
        
        if not contact or len(contact) == 0:
            errors["contact"] = "Por favor ingrese un contacto"
        
        return errors
    
    @classmethod
    def new(cls, name, adress, city, capacity, contact):
        """Create a new venue with validation"""
        errors = cls.validate(name, adress, city, capacity, contact)

        if errors:
            return False, errors

        venue = cls.objects.create(
            name = name,
            adress = adress,
            city = city,
            capacity = capacity,
            contact = contact
        )

        return True, venue

    def update(self, name, adress, city, capacity, contact):
        """Update venue fields"""
        
        if name is not None and len(name) != 0:
            self.name = name
        if adress is not None and len(adress) != 0:
            self.adress = adress
        if city is not None and len(city) != 0:
            self.city = city
        if capacity is not None and capacity >= 1:
            self.capacity = capacity
        if contact is not None and len(contact) != 0:
            self.contact = contact
        
        self.save()
        return True, self
    
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

        return True, category

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
    id = models.AutoField(primary_key=True)
    # Constants
    ACTIVE = 'ACTIVE'
    CANCELED = 'CANCELED'
    REPROGRAMED = 'REPROGRAMED'
    SOLD_OUT = 'SOLD_OUT'
    FINISHED = 'FINISHED'
    EVENT_STATES = [
        (ACTIVE, 'ACTIVO'),
        (CANCELED, 'CANCELADO'),
        (REPROGRAMED, 'REPROGRAMADO'),
        (SOLD_OUT, 'AGOTADO'),
        (FINISHED, 'FINALIZADO')
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    state = models.CharField(choices=EVENT_STATES, max_length=25, default="ACTIVE")

    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='venues')
    favorited_by = models.ManyToManyField(User, related_name="favorite_events", blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="events", null=True, blank=True)

    
    def __str__(self):
        return self.title

    def is_past(self):
        """Verifica si el evento ya pasó"""
        return self.scheduled_at < timezone.now()

    @classmethod
    def get_future_events(cls):
        """Retorna todos los eventos futuros ordenados por fecha"""
        return cls.objects.filter(scheduled_at__gt=timezone.now()).order_by('scheduled_at')

    def get_attendees(self):
        """Obtiene los usuarios inscriptos al evento a través de los tickets"""
        return User.objects.filter(tickets__event=self).distinct()

    @classmethod
    def validate(cls, title, description, scheduled_at):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"

        if description == "":
            errors["description"] = "Por favor ingrese una descripcion"

        return errors

    @classmethod
    def new(cls, title, description, scheduled_at, organizer, venue, category=None):
        errors = Event.validate(title, description, scheduled_at)

        if len(errors.keys()) > 0:
            return False, errors

        event = Event.objects.create(
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            organizer=organizer,
            venue=venue,
            category=category
        )

        return True, event

    def update(self, title=None, description=None, scheduled_at=None, organizer=None, venue=None, categories=None):
        #VERIFICO SI LA FECHA FUE CAMBIADA
        if scheduled_at and scheduled_at != self.scheduled_at:
            self.state = self.REPROGRAMED

        self.title = title or self.title
        self.description = description or self.description
        self.scheduled_at = scheduled_at or self.scheduled_at
        self.organizer = organizer or self.organizer
        self.venue = venue or self.venue
        self.category = category or self.category

        self.save()
        return True, self
    
   
    def available_tickets(self):
        aux = 0

        for t in self.tickets.all():
            aux = aux + t.quantity

        return self.venue.capacity - aux
    
    def auto_update_state(self):
        # ESTADO FINALIZADO SI LA FECHA YA PASO
        if self.scheduled_at < timezone.now():
            self.state = self.FINISHED
            self.save()
            return
        # ESTADO AGOTADO SI NO HAY MAS TICKETS DISPONIBLES
        if self.available_tickets() <= 0:
            self.state = self.SOLD_OUT
            self.save()
            return

    def get_average_rating(self):
        ratings = self.ratings.all()
        if not ratings:
            return 0
        return sum(rating.rating for rating in ratings) / len(ratings)

    def get_rating_count(self):
        return self.ratings.count()

class Ticket(models.Model):
    # Constants
    GENERAL = 'GENERAL'
    VIP = 'VIP'
    TICKETS_TYPE_CHOICES = [
        (GENERAL, 'General'),
        (VIP, 'VIP')
    ]

    # Atributes
    buy_date = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de compra'
    )
    ticket_code = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='Código del ticket'
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Cantidad'
    )
    type = models.CharField(
        max_length=25,
        choices=TICKETS_TYPE_CHOICES,
        verbose_name='Tipo de ticket'
    )

    # Foreign keys
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='tickets'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tickets'
    )

    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ['-buy_date']

    def __str__(self):
        return str(self.ticket_code)
    
    @classmethod
    def validate(cls, quantity, type, event, user):
        """Validate ticket data before creation"""
        errors = {}

        if quantity is None:
            errors["quantity"] = "La cantidad es requerida"
        elif not isinstance(quantity, int) or isinstance(quantity, bool):
            errors["quantity"] = "La cantidad debe ser un número entero válido"
        elif quantity < 1:
            errors["quantity"] = "La cantidad debe ser al menos 1"
        elif event and quantity > event.available_tickets():
            errors["quantity"] = f"No hay suficientes entradas disponibles. Solo quedan {event.available_tickets()} entradas."
        
        valid_types = [choice[0] for choice in cls.TICKETS_TYPE_CHOICES]
        if not type or type not in valid_types:
            errors["type"] = f"Tipo inválido. Opciones válidas: {', '.join(valid_types)}"
        
        if not event:
            errors["event"] = "Evento es requerido"
        elif event.available_tickets() <= 0:
            errors["event"] = "Lo sentimos, este evento ya no tiene entradas disponibles"
        
        if not user:
            errors["user"] = "Usuario es requerido"
        
        return errors
    
    @classmethod
    def new(cls, quantity, type, event, user):
        """Create a new ticket with validation"""
        errors = cls.validate(quantity, type, event, user)

        if errors:
            return False, errors

        try:
            ticket = cls.objects.create(
                quantity=quantity,
                type=type,
                event=event,
                user=user
            )

            print(ticket)
            return True, ticket
        except Exception as e:
            return False, {"error": f"Error al crear ticket: {str(e)}"}

    def update(self, buy_date, quantity, type, event, user):
        """Update ticket fields"""
        
        if buy_date is not None:
            self.buy_date = buy_date
        if quantity is not None:
            self.quantity = quantity
        if type is not None:
            self.type = type
        if event is not None:
            self.event = event
        if user is not None:
            self.user = user
        
        self.save()
        return True, self
    
    def is_recent_purchase(self, minutes=30):
        """Verifica si la compra fue hace menos de X minutos"""
        return (timezone.now() - self.buy_date) < timedelta(minutes=minutes)


class Rating(models.Model):
    title = models.CharField(max_length=200, default="Calificación")
    text = models.TextField(default="Sin comentarios")
    rating = models.IntegerField(default=5)  # Valor por defecto de 5 estrellas
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ratings')

    def __str__(self):
        return f"{self.title} - {self.event.title}"

    @classmethod
    def validate(cls, rating, text):
        errors = {}
        
        if not 1 <= rating <= 5:
            errors["rating"] = "La calificación debe estar entre 1 y 5"
            
        if len(text) > 500:
            errors["text"] = "El comentario no puede tener más de 500 caracteres"
            
        return errors

    @classmethod
    def new(cls, event, user, rating, text=""):
        errors = cls.validate(rating, text)
        
        if len(errors.keys()) > 0:
            return False, errors
            
        rating = cls.objects.create(
            event=event,
            user=user,
            rating=rating,
            text=text
        )
        
        return True, rating

    def update(self, rating, text):
        errors = self.validate(rating, text)
        
        if len(errors.keys()) > 0:
            return False, errors
            
        self.rating = rating
        self.text = text
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
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="notifications"
    )
    def __str__(self):
        return self.title
    
class RefundRequest(models.Model):
    approval = models.BooleanField(null=True, blank=True)
    approval_date = models.DateField(null=True, blank=True)
    ticket_code = models.CharField(max_length=255)
    reason = models.CharField(max_length=255)
    additional_details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_policy = models.BooleanField(default=False)
    event_name = models.CharField(max_length=255, blank=True, null=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="refund_requests")

    def __str__(self):
        return f"Refund Request for Ticket: {self.ticket_code}"


class SatisfactionSurvey(models.Model):
    SATISFACTION_CHOICES = [
        (1, "Muy insatisfecho"),
        (2, "Insatisfecho"),
        (3, "Neutro"),
        (4, "Satisfecho"),
        (5, "Muy satisfecho"),
    ]
    
    PURCHASE_EXPERIENCE_CHOICES = [
        ("muy_facil", "Muy fácil"),
        ("facil", "Fácil"),
        ("normal", "Normal"),
        ("dificil", "Difícil"),
        ("muy_dificil", "Muy difícil"),
    ]
    
    # Campos principales
    overall_satisfaction = models.IntegerField(
        choices=SATISFACTION_CHOICES,
        verbose_name="Satisfacción general"
    )
    purchase_experience = models.CharField(
        max_length=20,
        choices=PURCHASE_EXPERIENCE_CHOICES,
        verbose_name="Experiencia de compra"
    )
    would_recommend = models.BooleanField(
        verbose_name="¿Recomendarías este evento?"
    )
    comments = models.TextField(
        blank=True,
        null=True,
        verbose_name="Comentarios adicionales"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Relaciones
    ticket = models.OneToOneField(
        Ticket,
        on_delete=models.CASCADE,
        related_name="satisfaction_survey"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="satisfaction_surveys"
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="satisfaction_surveys"
    )

    class Meta:
        verbose_name = "Encuesta de Satisfacción"
        verbose_name_plural = "Encuestas de Satisfacción"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Encuesta de {self.user.username} - {self.event.title}"

    @classmethod
    def validate(cls, overall_satisfaction, purchase_experience, would_recommend, comments=None):
        """Validar datos de la encuesta"""
        errors = {}

        if not overall_satisfaction or overall_satisfaction not in [1, 2, 3, 4, 5]:
            errors["overall_satisfaction"] = "Debes seleccionar un nivel de satisfacción"

        if not purchase_experience or purchase_experience not in ["muy_facil", "facil", "normal", "dificil", "muy_dificil"]:
            errors["purchase_experience"] = "Debes seleccionar una experiencia de compra"

        if would_recommend is None:
            errors["would_recommend"] = "Debes indicar si recomendarías el evento"

        if comments and len(comments) > 500:
            errors["comments"] = "Los comentarios no pueden tener más de 500 caracteres"

        return errors

    @classmethod
    def new(cls, ticket, user, event, overall_satisfaction, purchase_experience, would_recommend, comments=None):
        """Crear nueva encuesta con validación"""
        errors = cls.validate(overall_satisfaction, purchase_experience, would_recommend, comments)

        if errors:
            return False, errors

        # Verificar que no exista ya una encuesta para este ticket
        if cls.objects.filter(ticket=ticket).exists():
            return False, {"ticket": "Ya existe una encuesta para este ticket"}

        try:
            survey = cls.objects.create(
                ticket=ticket,
                user=user,
                event=event,
                overall_satisfaction=overall_satisfaction,
                purchase_experience=purchase_experience,
                would_recommend=would_recommend,
                comments=comments
            )
            return True, survey
        except Exception as e:
            return False, {"error": f"Error al crear encuesta: {str(e)}"}

    def get_satisfaction_display_with_icon(self):
        """Obtener el display de satisfacción con ícono"""
        icons = {
            1: "😞",
            2: "😐",
            3: "😶",
            4: "😊",
            5: "😁"
        }
        return f"{icons.get(self.overall_satisfaction, '')} {self.get_overall_satisfaction_display()}"
