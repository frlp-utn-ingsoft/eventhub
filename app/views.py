import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Event, User, Venue
from .forms import VenueForm


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


from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Event, Venue

@login_required
def event_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        # Datos del evento
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")
        venue_id = request.POST.get("venue")

        # Datos del nuevo Venue (si se crea uno nuevo)
        new_venue_name = request.POST.get("new_venue_name")
        new_venue_address = request.POST.get("new_venue_address")
        new_venue_city = request.POST.get("new_venue_city")
        new_venue_capacity = request.POST.get("new_venue_capacity")
        new_venue_contact = request.POST.get("new_venue_contact")

        # Crear el nuevo Venue si se proporcionaron datos
        if new_venue_name and new_venue_address and new_venue_city:
            venue = Venue.objects.create(
                name=new_venue_name,
                address=new_venue_address,
                city=new_venue_city,
                capacity=new_venue_capacity,
                contact=new_venue_contact,
            )
        else:
            venue = get_object_or_404(Venue, pk=venue_id)

        # Crear o actualizar el evento
        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")
        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if id is None:
            Event.objects.create(
                title=title,
                description=description,
                scheduled_at=scheduled_at,
                organizer=user,
                venue=venue,
            )
        else:
            event = get_object_or_404(Event, pk=id)
            event.title = title
            event.description = description
            event.scheduled_at = scheduled_at
            event.venue = venue
            event.save()

        return redirect("events")

    # Si es una solicitud GET, cargar el formulario
    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    venues = Venue.objects.all()
    return render(
        request,
        "app/event_form.html",
        {"event": event, "venues": venues, "user_is_organizer": user.is_organizer},
    )


@login_required
def venue_list(request):
    if not request.user.is_organizer:
        return redirect("events")  # Redirigir a la lista de eventos si no es organizador
    venues = Venue.objects.all()
    return render(request, "app/venue.html", {"venues": venues})

@login_required
def venue_form(request, id=None):
    # Verificar si el usuario es organizador
    if not request.user.is_organizer:
        return redirect("events")  # Redirigir a la lista de eventos si no es organizador

    # Si se proporciona un ID, obtener la ubicación existente
    if id:
        venue = get_object_or_404(Venue, pk=id)
    else:
        venue = None

    # Procesar el formulario
    if request.method == "POST":
        form = VenueForm(request.POST, instance=venue)
        if form.is_valid():
            form.save()  # Guardar la nueva ubicación o actualizar la existente
            return redirect("venue_list")  # Redirigir a la lista de ubicaciones
    else:
        form = VenueForm(instance=venue)

    # Renderizar el formulario
    return render(request, "app/venue_form.html", {"form": form, "venue": venue})

@login_required
def venue_detail(request, id):
    if not request.user.is_organizer:
        return redirect("events")  # Redirigir a la lista de eventos si no es organizador
    venue = get_object_or_404(Venue, pk=id)
    return render(request, "app/venue_detail.html", {"venue": venue})

@login_required
def venue_delete(request, id):
    if not request.user.is_organizer:
        return redirect("events")  # Redirigir a la lista de eventos si no es organizador
    venue = get_object_or_404(Venue, pk=id)
    if request.method == "POST":
        venue.delete()
        return redirect("venue_list")
    return render(request, "app/venue_confirm_delete.html", {"venue": venue})