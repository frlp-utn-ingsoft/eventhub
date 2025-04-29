import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Event, Rating, Rating_Form, User


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
    event = get_object_or_404(Event, pk=id)
    return render(request, "app/event_detail.html", {"event": event})


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
















































































































































































































































































































































































































































@login_required
def event_rating(request, id):
    evento = get_object_or_404(Event, pk=id)
    resenas = Rating.objects.filter(evento=evento)
    cantidad_resenas = resenas.count()

    try:
        resena_existente = Rating.objects.get(usuario=request.user, evento=evento)
        editando = True
    except Rating.DoesNotExist:
        resena_existente = None
        editando = False
        
    if request.method == 'POST':
        if 'guardar' in request.POST:
            form = Rating_Form(request.POST, instance=resena_existente)
            if form.is_valid():
                nueva_resena = form.save(commit=False)
                nueva_resena.usuario = request.user 
                nueva_resena.evento = evento
                nueva_resena.save()
                messages.success(request, "¡Tu reseña fue guardada exitosamente!")
            return redirect('event_rating', id=evento.id) # type: ignore
        
        elif 'eliminar' in request.POST and resena_existente:
            resena_existente.delete()
            messages.success(request, "¡Tu reseña fue eliminada exitosamente!")
            return redirect('event_rating', id=evento.id) # type: ignore

        elif 'cancelar' in request.POST:
            form = Rating_Form()
            return redirect('event_rating', id=evento.id) #type: ignore

    form = Rating_Form(instance=resena_existente)            
        
    return render(request, 'app/event_rating.html', {
        'evento': evento,
        'ratings' : resenas,
        'form': form,
        'editando': editando,
        'cantidad_resenas': cantidad_resenas
    })