from pyexpat.errors import messages

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render


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

CALIFICACIONES = [(i, f"{i} ⭐") for i in range(1,6)]

class Rating(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    evento = models.ForeignKey(Event, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=255)
    texto = models.TextField(blank=True)
    calificacion = models.IntegerField(choices=CALIFICACIONES) 
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        #Con unique se busca que solo el usuario pueda hacer una sola calificacion
        unique_together = ('usuario', 'evento')
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f'{self.usuario} - {self.evento} ({self.calificacion}⭐)'

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['titulo', 'calificacion', 'texto']
        widgets = {
            'calificacion' : forms.RadioSelect(choices=[(i, f'{i} ⭐') for i in range(1, 6)]),
            'texto' : forms.Textarea(attrs={'rows': 4, 'placeholder': 'Comparte tu experiencia...'}),
        }
    
@login_required
def detalle_evento(request, evento_titulo):
    evento = get_object_or_404(Event, pk=evento_titulo)
    resenas = Rating.objects.filter(evento=evento)

    try:
        resena_existente = Rating.objects.get(usuario=request.user, evento=evento)
        form = RatingForm(instance=resena_existente)
        editando = True
    except Rating.DoesNotExist:
        resena_existente = None
        form = RatingForm()
        editando = False
        
    if request.method == 'POST':
        form = RatingForm(request.POST, instance=resena_existente)
        if form.is_valid():
            nueva_resena = form.save(commit=False)
            nueva_resena.usuario = request.user 
            nueva_resena.evento = evento
            nueva_resena.save()
            messages.success(request, "¡Tu reseña fue guardada exitosamente!") # type: ignore
            return redirect('detalle_evento', evento_titulo=evento.title)
        
    return render(request, 'app/detalle_evento.html', {
        'evento': evento,
        'ratings' : resenas,
        'form': form,
        'editando': editando
    })

def eliminar_resena(request, resena_id):
    resena = get_object_or_404(Rating, id=resena_id)
    if resena.usuario == request.user or request.user.is_staff:
        resena.delete()
    return redirect('detalle_evento', evento_titulo=resena.evento.title)