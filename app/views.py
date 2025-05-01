import datetime

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CommentForm
from .models import Comment, Event, User


def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("username")
        is_organizer = request.POST.get("is-organizer") is not None
        password = request.POST.get("password")
        password_confirm = request.POST.get("password-confirm")

        errors = User.validate_new_user(email, username, password, password_confirm)

        if len(errors) > 0:
            return render(
                request,
                "accounts/register.html",
                {
                    "errors": errors,
                    "data": request.POST,
                },
            )
        else:
            user = User.objects.create_user(
                email=email, username=username, password=password, is_organizer=is_organizer
            )
            login(request, user)
            return redirect("events")

    return render(request, "accounts/register.html", {})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(
                request, "accounts/login.html", {"error": "Usuario o contraseña incorrectos"}
            )

        login(request, user)
        return redirect("events")

    return render(request, "accounts/login.html")


def home(request):
    return render(request, "home.html")


@login_required
def events(request):
    events = Event.objects.all().order_by("scheduled_at")
    return render(
        request,
        "app/events.html",
        {"events": events, "user_is_organizer": request.user.is_organizer},
    )
@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, id=id)
    comments = Comment.objects.filter(event=event)
    form = CommentForm()  # Formulario para nuevo comentario

    editing_comment_id = None
    editing_form = None

    if request.method == "POST":
        if 'create_comment' in request.POST:
            # Crear nuevo comentario
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.user = request.user
                comment.event = event
                comment.save()
                return redirect('event_detail', id=event.pk)
        elif 'edit_comment' in request.POST:
            # Editar comentario existente
            comment_id = request.POST.get('comment_id')
            comment = get_object_or_404(Comment, id=comment_id, user=request.user)
            editing_form = CommentForm(request.POST, instance=comment)
            editing_comment_id = comment.pk

            if editing_form.is_valid():
                editing_form.save()
                return redirect('event_detail', id=event.pk)

    return render(
        request,
        'app/event_detail.html',
        {
            'event': event,
            'comments': comments,
            'form': form,
            'editing_comment_id': editing_comment_id,
            'editing_form': editing_form,
        }
    )


@login_required
def event_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        event = get_object_or_404(Event, pk=id)
        event.delete()
        return redirect("events")

    return redirect("events")


@login_required
def event_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if id is None:
            Event.new(title, description, scheduled_at, request.user)
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, request.user)

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    return render(
        request,
        "app/event_form.html",
        {"event": event, "user_is_organizer": request.user.is_organizer},
    )
# 🟢 Vista para listar todos los comentarios de un evento
def comment_list(request, event_id):
    # Obtener el evento mediante su ID, o mostrar un error 404 si no existe
    event = get_object_or_404(Event, id=event_id)
    
    # Obtener todos los comentarios asociados a este evento
    comments = Comment.objects.filter(event=event)
    
    # Renderizar el template 'comment_list.html' y pasarle el evento y los comentarios
    return render(request, 'comments/comment_list.html', {'event': event, 'comments': comments})


# 🔵 Vista para crear un comentario en un evento
@login_required  # Asegura que el usuario esté autenticado
def comment_create(request, event_id):
    # Obtener el evento correspondiente al ID, o mostrar un error 404 si no existe
    event = get_object_or_404(Event, id=event_id)

    # Si el método de la solicitud es POST, significa que el usuario está enviando el formulario
    if request.method == 'POST':
        form = CommentForm(request.POST)  # Crear el formulario con los datos enviados

        # Verificar si el formulario es válido
        if form.is_valid():
            comment = form.save(commit=False)  # Crear el comentario sin guardarlo aún
            comment.user = request.user  # Asignar el usuario logueado al comentario
            comment.event = event  # Asociar el comentario con el evento correspondiente
            comment.save()  # Guardar el comentario en la base de datos
            # Redirigir al usuario a la lista de comentarios del evento
            return redirect('comment_list', event_id=event.pk)
    else:
        form = CommentForm()  # Si no es POST, crear un formulario vacío

    # Renderizar el template 'comment_form.html' y pasarle el formulario y el evento
    return render(request, 'comments/comment_form.html', {'form': form, 'event': event})


# 🟠 Vista para editar un comentario
@login_required  # Asegura que solo los usuarios autenticados puedan editar comentarios
def comment_edit(request, pk):
    # Obtener el comentario mediante su ID (primary key - pk), o mostrar error 404 si no existe
    comment = get_object_or_404(Comment, pk=pk)

    # Si el usuario no es el autor del comentario, redirigir a la lista de comentarios
    if request.user != comment.user:
        return redirect('comment_list', event_id=comment.event.pk)

    # Si el método de la solicitud es POST, significa que el usuario está enviando el formulario de edición
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)  # Crear formulario con los datos del comentario existente

        # Verificar si el formulario es válido
        if form.is_valid():
            form.save()  # Guardar los cambios en el comentario
            return redirect('comment_list', event_id=comment.event.pk)  # Redirigir a la lista de comentarios
    else:
        form = CommentForm(instance=comment)  # Si no es POST, mostrar el formulario con los datos actuales del comentario

    # Renderizar el template 'comment_form.html' para editar el comentario
    return render(request, 'comments/comment_form.html', {'form': form, 'event': comment.event})


# 🔴 Vista para eliminar un comentario
@login_required  # Asegura que solo los usuarios autenticados puedan eliminar comentarios
def comment_delete(request, pk):
    # Obtener el comentario mediante su ID (primary key - pk), o mostrar error 404 si no existe
    comment = get_object_or_404(Comment, pk=pk)

    # Comprobar si el usuario es el autor del comentario o si es un organizador (usando is_staff)
    is_organizer = request.user.is_staff  # Aquí se puede usar otro sistema de permisos si lo prefieres

    # Si el usuario no es el autor ni un organizador, redirigir a la lista de comentarios
    if request.user != comment.user and not is_organizer:
        return redirect('comment_list', event_id=comment.event.pk)

    # Si el método es POST, eliminar el comentario
    if request.method == 'POST':
        event_id = comment.event.pk  # Guardar el ID del evento para redirigir después
        comment.delete()  # Eliminar el comentario de la base de datos
        return redirect('comment_list', event_id=event_id)  # Redirigir a la lista de comentarios del evento

    # Si el método no es POST, mostrar la confirmación de eliminación
    return render(request, 'comments/comment_confirm_delete.html', {'comment': comment})