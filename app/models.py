import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError, IntegrityError

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
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='venues')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="events", null=True, blank=True)

    def __str__(self):
        return self.title

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

    def update(self, title=None, description=None, scheduled_at=None, organizer=None, venue=None, category=None):
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

class Discount(models.Model):
    code = models.CharField(
        max_length=8,
        unique=True,
        editable=False,
        blank=True,
        null=True,
        verbose_name='Código'
    )
    
    multiplier = models.FloatField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(1)
        ],
        verbose_name='Multiplicador'
    )

    class Meta:
        verbose_name = 'Descuento'
        verbose_name_plural = 'Descuentos'

    def __str__(self):
        return f"{self.code or 'Sin código'} - {self.multiplier*100}%"

    def clean(self):
        """Validación a nivel de modelo"""
        if self.code and len(self.code) != 8:
            raise ValidationError({'code': 'El código debe tener exactamente 8 caracteres'})
        
        if self.multiplier is None:
            raise ValidationError({'multiplier': 'El multiplicador es requerido'})

    def save(self, *args, **kwargs):
        """Generación automática de código si no se proporciona"""
        if not self.code:
            self.code = self.generate_discount_code()
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def generate_discount_code(cls):
        """Genera un código único de 8 caracteres"""
        code = uuid.uuid4().hex[:8].upper()
        while cls.objects.filter(code=code).exists():
            code = uuid.uuid4().hex[:8].upper()
        return code

    @classmethod
    def validate(cls, code=None, multiplier=None):
        """Validación previa a la creación"""
        errors = {}
        
        if code is not None and code != '':
            if not isinstance(code, str):
                errors['code'] = 'El código debe ser texto'
            elif len(code) != 8:
                errors['code'] = 'El código debe tener 8 caracteres'
        
        if multiplier is None:
            errors['multiplier'] = 'Multiplicador requerido'
        else:
            try:
                multiplier = float(multiplier)
                if not (0 <= multiplier <= 1):
                    errors['multiplier'] = 'Debe estar entre 0 y 1'
            except (TypeError, ValueError):
                errors['multiplier'] = 'Debe ser un número válido'
        
        return errors

    @classmethod
    def new(cls, code=None, multiplier=None):
        """Crea un nuevo descuento con validación"""
        errors = cls.validate(code, multiplier)
        if errors:
            return False, errors
            
        try:
            discount = cls(code=code, multiplier=multiplier)
            discount.full_clean()
            discount.save()

            return True, discount
        
        except IntegrityError:
            return False, {'error': 'El código ya existe'}
        except ValidationError as e:
            return False, e.message_dict
        except Exception as e:
            return False, {'error': str(e)}

    def update(self, code=None, multiplier=None):
        """Update discount fields"""
        errors = {}
        
        if code is not None:
            if not isinstance(code, str):
                errors["code"] = "El código debe ser una cadena de texto."
            elif len(code) != 8:
                errors["code"] = "El código de descuento debe tener exactamente 8 caracteres."
            elif Discount.objects.filter(code=code).exclude(pk=self.id).exists():
                errors["code"] = "Este código ya está en uso por otro descuento."
        
        if multiplier is not None:
            try:
                multiplier = float(multiplier)
                if multiplier > 1:
                    errors["multiplier"] = "El multiplicador debe ser como máximo 1."
                elif multiplier < 0:
                    errors["multiplier"] = "El multiplicador debe ser al menos 0."
            except (TypeError, ValueError):
                errors["multiplier"] = "El multiplicador debe ser un número válido."
        
        if errors:
            return False, errors
        
        try:
            if code is not None:
                self.code = code
            
            if multiplier is not None:
                self.multiplier = multiplier
            
            self.save()
            
            return True, self
        
        except IntegrityError:
            return False, {"error": "Error de integridad, posiblemente el código ya existe"}
        except Exception as e:
            return False, {"error": f"Error al actualizar el descuento: {str(e)}"}




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

    discount = models.ForeignKey(
        Discount,
        on_delete=models.CASCADE,
        related_name='discounts'
    )

    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ['-buy_date']

    def __str__(self):
        return str(self.ticket_code)
    
    @classmethod
    def validate(cls, quantity, type, event, user, discount=None):
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
        
        if discount and not isinstance(discount, Discount):
            errors["discount"] = "El descuento debe ser una instancia válida del modelo Discount"            

        return errors
    
    @classmethod
    def new(cls, quantity, type, event, user, discount=None):
        """Create a new ticket with validation"""
        errors = cls.validate(quantity, type, event, user, discount)

        if errors:
            return False, errors

        try:
            ticket = cls.objects.create(
                quantity=quantity,
                type=type,
                event=event,
                user=user,
                discount=discount
            )

            print(ticket)
            return True, ticket
        except Exception as e:
            return False, {"error": f"Error al crear ticket: {str(e)}"}

    def update(self, buy_date, quantity, type, event, user, discount=None):
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
        if discount is not None:
            self.discount = discount
        
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
