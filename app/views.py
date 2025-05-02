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
    comments = Comment.objects.filter(event=event, is_deleted=False).order_by('-created_at')
    form = CommentForm()

    return render(request, 'app/event_detail.html', {
        'event': event,
        'comments': comments,
        'form': form,
    })

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
    event = get_object_or_404(Event, id=event_id)
    comments = Comment.objects.filter(event=event)
    return render(request, 'comments/comment_list.html', {'event': event, 'comments': comments})

@login_required
def comment_create(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.event = event
            comment.save()
    return redirect('event_detail', id=event.pk)

@login_required
def comment_update(request, pk):
    comment = get_object_or_404(Comment, pk=pk)

    if comment.user != request.user:
        return redirect('event_detail', id=comment.event.pk)

    if request.method == "POST":
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('event_detail', id=comment.event.pk)
    else:
        form = CommentForm(instance=comment)  # renderiza el formulario con datos actuales

    return render(request, 'comments/comment_edit.html', {
    'form': form,
    'event': comment.event,
    'original_comment': comment
})



# Eliminar un comentario (lógico, solo POST)
@login_required
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    event = comment.event

    is_author = request.user == comment.user
    is_event_organizer = request.user == event.organizer

    if not (is_author or is_event_organizer):
        return redirect('event_detail', id=event.pk)

    if request.method == 'POST':
        comment.is_deleted = True
        comment.save()

        if is_event_organizer and not is_author:
            return redirect('organizer_comments')  # vista que vos definas
        else:
            return redirect('event_detail', id=event.pk)

    # Si alguien accede por GET, redirigir (no permitir)
    return redirect('event_detail', id=event.pk)
@login_required
def organizer_comments(request):
    # 1️⃣ Solo los organizadores pueden entrar
    if not request.user.is_organizer:
        return redirect("events")  # redirige al listado de eventos

    # 2️⃣ Traer todos los eventos creados por este organizador
    eventos = Event.objects.filter(organizer=request.user)

    # 3️⃣ Filtrar todos los comentarios de esos eventos
    comentarios = Comment.objects.filter(
        event__in=eventos
    ).select_related("event", "user").order_by("-created_at")

    # 4️⃣ Renderizar el template con la lista de comentarios
    return render(request, "comments/organizer_comments.html", {
        "comentarios": comentarios
    })

@login_required
def comment_hard_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)

    # Solo el organizador del evento puede eliminar completamente
    if request.user != comment.event.organizer:
        return redirect('events')

    if request.method == 'POST':
        comment.delete()  # Borrado total
        return redirect('organizer_comments')

    return redirect('organizer_comments')

