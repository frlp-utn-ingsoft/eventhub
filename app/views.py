import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages
from .models import Venue, Event, User, Rating
from .forms import VenueForm, RatingForm


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
def rating_create(request, id):
    if request.user.is_organizer:
        messages.error(request, "Los organizadores no pueden dejar calificaciones.")
        return redirect("event_detail", id=id)

    if request.method == "POST":
        event = get_object_or_404(Event, pk=id)
        title = request.POST.get("title", "").strip()
        score = request.POST.get("score")
        comment = request.POST.get("comment", "").strip()

        Rating.objects.create(
            event=event, user=request.user, title=title, score=score, comment=comment
        )

    return redirect("event_detail", id=id)


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    ratings = Rating.objects.filter(event=event)
    user_is_organizer = event.organizer == request.user

    rating_to_edit = None
    rating_id = request.GET.get('rating_id') or request.POST.get('rating_id')

    if rating_id:
        rating_to_edit = get_object_or_404(Rating, pk=rating_id, event=event)
        if user_is_organizer or rating_to_edit.user != request.user:
            return redirect('event_detail', id=id)

    if request.method == 'POST':
        if rating_to_edit:
            form = RatingForm(request.POST, instance=rating_to_edit)
        else:
            if user_is_organizer:
                return redirect('event_detail', id=id)
            form = RatingForm(request.POST)

        if form.is_valid():
            new_rating = form.save(commit=False)
            new_rating.event = event
            new_rating.user = request.user
            new_rating.save()
            return redirect('event_detail', id=id)
    else:
        form = RatingForm(instance=rating_to_edit)

    context = {
        'event': event,
        'ratings': ratings,
        'form': form,
        'rating_to_edit': rating_to_edit,
        'user_is_organizer': user_is_organizer,
        'show_rating_form': not user_is_organizer
    }
    return render(request, 'app/event_detail.html', context)


@login_required
def rating_delete(request, id, rating_id):
    event = get_object_or_404(Event, pk=id)
    rating = get_object_or_404(Rating, pk=rating_id, event=event)
    if request.user == rating.user or request.user.is_organizer:
        if request.method == "POST":
            rating.delete()
            return redirect("event_detail", id=id)
    return redirect("event_detail", id=id)


@login_required
def event_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")

    event = get_object_or_404(Event, pk=id)

    if request.method == "POST":
        event.delete()
        return redirect("events")

    return redirect("event_detail", id=id)


@login_required
def event_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    event = None

    if id is not None:
        event = get_object_or_404(Event, pk=id)

    # Obtener solo los venues del organizador
    venues = Venue.objects.filter(organizer=request.user)
    today = timezone.localtime().date()
    min_date = today + datetime.timedelta(days=1)

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")
        venue_id = request.POST.get("venue")

        # Validar campos obligatorios
        if not venue_id:
            return render(
                request,
                "app/event_form.html",
                {
                    "event": event,
                    "user_is_organizer": user.is_organizer,
                    "min_date": min_date,
                    "venues": venues,
                    "error": "Debe seleccionar un lugar para el evento.",
                },
            )

        [year, month, day] = map(int, date.split("-"))
        [hour, minutes] = map(int, time.split(":"))
        scheduled_at = timezone.make_aware(datetime.datetime(year, month, day, hour, minutes))

        if scheduled_at.date() <= today:
            return render(
                request,
                "app/event_form.html",
                {
                    "event": event,
                    "user_is_organizer": user.is_organizer,
                    "min_date": min_date,
                    "venues": venues,
                    "error": "La fecha debe ser a partir de mañana.",
                },
            )

        venue = get_object_or_404(Venue, pk=venue_id, organizer=user)

        if id is None:
            Event.new(title, description, scheduled_at, user, venue)
        else:
            event.update(title, description, scheduled_at, user, venue)

        return redirect("events")

    return render(
        request,
        "app/event_form.html",
        {
            "event": event,
            "user_is_organizer": user.is_organizer,
            "min_date": min_date,
            "venues": venues,
            "no_venues": not venues.exists(),  # <- Para mostrar un mensaje en el template
        },
    )






########


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from .models import Venue
from .forms import VenueForm

# LISTA DE VENUES DEL ORGANIZADOR (u opcionalmente visibles para todos)
@login_required
def venue_list(request):
    if request.user.is_organizer:
        venues = Venue.objects.filter(organizer=request.user)
    else:
        venues = Venue.objects.all()  # si querés que los usuarios normales puedan ver todas
    return render(request, 'venues/venue_list.html', {'venues': venues})


# CREAR
@login_required
def create_venue(request):
    if not request.user.is_organizer:
        return HttpResponseForbidden("Solo los organizadores pueden crear ubicaciones.")
    
    form = VenueForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        venue = form.save(commit=False)
        venue.organizer = request.user
        venue.save()
        return redirect('venue_list')
    return render(request, 'venues/create_venue.html', {'form': form})


# EDITAR
@login_required
def edit_venue(request, venue_id):
    venue = get_object_or_404(Venue, id=venue_id)

    if not request.user.is_organizer or venue.organizer != request.user:
        return HttpResponseForbidden("No tenés permiso para editar esta ubicación.")
    
    form = VenueForm(request.POST or None, instance=venue)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('venue_list')
    return render(request, 'venues/edit_venue.html', {'form': form})


# ELIMINAR
@login_required
def delete_venue(request, venue_id):
    venue = get_object_or_404(Venue, id=venue_id)

    if not request.user.is_organizer or venue.organizer != request.user:
        return HttpResponseForbidden("No tenés permiso para eliminar esta ubicación.")
    
    if request.method == 'POST':
        venue.delete()
        return redirect('venue_list')
    return render(request, 'venues/delete_venue.html', {'venue': venue})


# DETALLE (acceso abierto para todos)
@login_required
def venue_detail(request, venue_id):
    venue = get_object_or_404(Venue, id=venue_id)
    return render(request, 'venues/venue_detail.html', {'venue': venue})

